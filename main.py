import json
import argparse
import numpy as np
import sys
import os


class UnicodeTable:
    
    HORIZONTAL = u'\u2500'
    VERTICAL = u'\u2502'
    LEFT_DOWN = u'\u2510'
    RIGHT_DOWN = u'\u250C'
    LEFT_UP = u'\u2518'
    RIGHT_UP = u'\u2514'
    CROSS = u'\u253C'
    VERTICAL_LEFT = u'\u2524'
    VERTICAL_RIGHT = u'\u251C'
    HORIZONTAL_UP = u'\u2534'
    HORIZONTAL_DOWN = u'\u252C'

    def __init__(self,row_num,col_num,pad_width,pad_height,item_width,item_height,row_div_stride=1,col_div_stride=1):
        self.row_num = row_num
        self.col_num = col_num
        self.item_width = item_width
        self.item_height = item_height
        self.pad_width = pad_width
        self.pad_height = pad_height
        self.row_div_stride = row_div_stride
        self.col_div_stride = col_div_stride

        total_width = ((item_width+2*pad_width)*col_num)+(col_num // col_div_stride) +1
        total_height = ((item_height+2*pad_height)*row_num)+(row_num // row_div_stride)+1

        self.data = np.ndarray(shape=(total_height,total_width), dtype=np.dtype('U1'))
        self.data[:,:] = u' '
        self.data[0,0] = self.RIGHT_DOWN
        self.data[0,-1] = self.LEFT_DOWN
        self.data[-1,0] = self.RIGHT_UP
        self.data[-1,-1] = self.LEFT_UP
        vertical_stride = ((item_height+pad_height*2)*row_div_stride)+1
        horizontal_stride = ((item_width+pad_width*2)*col_div_stride)+1
        self.data[0:total_height:vertical_stride,1:-1] = self.HORIZONTAL
        self.data[1:-1,0:total_width:horizontal_stride] = self.VERTICAL
        self.data[vertical_stride:-vertical_stride:vertical_stride,
            horizontal_stride:-horizontal_stride:horizontal_stride] = self.CROSS
        self.data[0,horizontal_stride:-horizontal_stride:horizontal_stride] = self.HORIZONTAL_DOWN
        self.data[-1,horizontal_stride:-horizontal_stride:horizontal_stride] = self.HORIZONTAL_UP
        self.data[vertical_stride:-vertical_stride:vertical_stride,0] = self.VERTICAL_RIGHT
        self.data[vertical_stride:-vertical_stride:vertical_stride,-1] = self.VERTICAL_LEFT

    def __setitem__(self,key,value):
        row_idx,col_idx = key
        # turn value into utf-32 array
        buf = np.frombuffer(str(value).encode('utf-32le'),dtype='U1')
        # calculate cell range
        y_start = (self.item_height+self.pad_height*2)*row_idx+(row_idx//self.row_div_stride)+self.pad_height+1
        y_end = y_start + self.item_height
        x_start = (self.item_width+self.pad_width*2)*col_idx+(col_idx//self.col_div_stride)+self.pad_width+1
        x_end = x_start + self.item_width
        # set range of cell to reshaped utf-32 array
        if buf.shape[0] > self.item_height*self.item_width:
            buf = buf[:self.item_height*self.item_width]
        self.data[y_start:y_end,x_start:x_end] = buf.reshape((self.item_height,self.item_width))


    def get_char_dim(self):
        return self.data.shape


    def __str__(self):
        result = ""
        for row in self.data:
            result += row.tobytes().decode(encoding='utf-32le', errors='strict') + '\n'
            # sys.stdout.buffer.write(row.tobytes())
            # sys.stdout.buffer.write(b'\n')

            # result += row.tostring()
            # result += '\n'
        return result

"""
def convert_data_to_ascii(data):
    result = ""
    result += (RIGHT_DOWN+3*HORIZONTAL+HORIZONTAL_DOWN+3*HORIZONTAL+HORIZONTAL_DOWN+3*HORIZONTAL+LEFT_DOWN+'\n')
    for y1 in range(0,3):
        for y2 in range(0,3):
            y = y1+y2
            result += VERTICAL
            for x1 in range(0,3):
                for x2 in range(0,3):
                    x = x1 + x2

                    result += HORIZONTAL
            
            result += VERTICAL+'\n'
    result += (RIGHT_UP+3*HORIZONTAL+HORIZONTAL_UP+3*HORIZONTAL+HORIZONTAL_UP+3*HORIZONTAL+LEFT_UP+'\n')
    return result
"""

def data_to_superposition(data,superpos):
    superpos[:,:,:] = True
    for y in range(0,9):
        for x in range(0,9):
            number = data[x,y]
            if number != 0:
                superpos[x,y,:] = False
                superpos[x,y,number-1] = True
    

def apply_rules(superpos,level=1):
    old_superpos = superpos.copy()
    if level > 0:
        for idx in np.argwhere(np.sum(superpos, axis=2) == 1):
            number = np.argwhere(superpos[idx[0],idx[1]] == True).flatten()
            # No other number of same kind in same row
            superpos[idx[0],:,number] = False
            # No other number of same kind in same column
            superpos[:,idx[1],number] = False
            # No other number of same kind in same 3x3 cell
            cell_y = idx[0] // 3
            cell_x = idx[1] // 3
            superpos[cell_y*3:cell_y*3+3,cell_x*3:cell_x*3+3,number] = False
            # Reset number
            superpos[idx[0],idx[1],number] = True
    if level > 1:
        pass
    return np.sum(np.logical_xor(superpos,old_superpos))



def collapse(superpos):
    print(np.argwhere(np.sum(superpos,axis=2) == 1))
    new_data = np.zeros((9,9),dtype='uint8')
    indices=np.argwhere(np.sum(superpos,axis=2) == 1)
    print(superpos[:3,:3])
    print(np.unique(superpos[:3,:3], axis=2, return_index=True, return_counts=True, return_inverse=True))
    return new_data

def data_to_table(data, table):
    for y in range(0,9):
        for x in range(0,9):
            value = data[x][y]
            if value != 0:
                table_column = (y*3)+(value-1)%3
                table_row = (x*3)+(value-1) // 3
                table[table_row,table_column] = data[x][y]

def superpos_to_table(superpos, table):
    for y in range(0,table.col_num):
        for x in range(table.row_num):
            table[x,y] = u' '
    for y in range(0,9):
        for x in range(0,9):
            value_arr = superpos[x][y]
            for value in np.argwhere(value_arr == True).flatten():
                table_column = (y*3)+(value)%3
                table_row = (x*3)+(value) // 3
                table[table_row,table_column] = value+1

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
                    prog='Sudoku Solver',
                    description='This solver takes a JSON format input 2D array of a Sudoku puzzle and solves it'
                    )

    parser.add_argument('filename')
    args = parser.parse_args()

    data = None
    with open(args.filename) as f:
        data = np.array(json.load(f),dtype='uint8')
    
    table = UnicodeTable(27,27,1,0,1,1,3,3)
    data_to_table(data, table)
    print(table)

    superpos = np.ndarray((9,9,9),dtype='bool')
    data_to_superposition(data,superpos)
    while True:
        changes = apply_rules(superpos)
        print(changes)
        if changes == 0:
            break
    superpos_to_table(superpos,table)
    print(table)
    # collapse(superpos)


    


