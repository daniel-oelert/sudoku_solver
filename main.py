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

    def __init__(self,row_num,col_num,pad_width,pad_height,item_width,item_height):
        self.row_num = row_num
        self.col_num = col_num
        self.item_width = item_width
        self.item_height = item_height
        self.pad_width = pad_width
        self.pad_height = pad_height

        total_width = ((item_width+2*pad_width)*col_num)+col_num+1
        total_height = ((item_height+2*pad_height)*row_num)+row_num+1

        self.data = np.ndarray(shape=(total_height,total_width), dtype=np.dtype('U1'))
        self.data[::,::] = u' '
        self.data[0,0] = self.RIGHT_DOWN
        self.data[0,-1] = self.LEFT_DOWN
        self.data[-1,0] = self.RIGHT_UP
        self.data[-1,-1] = self.LEFT_UP
        self.data[0:total_height:item_height+pad_height*2+1,1:-1] = self.HORIZONTAL
        self.data[1:-1,0:total_width:item_width+pad_width*2+1] = self.VERTICAL
        self.data[item_height+pad_height*2+1:-(item_height+pad_height*2+1):item_height+pad_height*2+1,
            item_width+pad_width*2+1:-(item_width+pad_width*2+1):item_width+pad_width*2+1] = self.CROSS
        self.data[0,item_width+pad_width*2+1:-(item_width+pad_width*2+1):item_width+pad_width*2+1] = self.HORIZONTAL_DOWN
        self.data[-1,item_width+pad_width*2+1:-(item_width+pad_width*2+1):item_width+pad_width*2+1] = self.HORIZONTAL_UP
        self.data[item_height+pad_height*2+1:-(item_height+pad_height*2+1):item_height+pad_height*2+1,0] = self.VERTICAL_RIGHT
        self.data[item_height+pad_height*2+1:-(item_height+pad_height*2+1):item_height+pad_height*2+1,-1] = self.VERTICAL_LEFT

    def __setitem__(self,key,value):
        row_idx,col_idx = key
        # turn value into utf-32 array
        buf = np.frombuffer(str(value).encode('utf-32le'),dtype='U1')
        # calculate cell range
        y_start = (self.item_height+self.pad_height*2+1)*row_idx+self.pad_height+1
        y_end = y_start + self.item_height
        x_start = (self.item_width+self.pad_width*2+1)*col_idx+self.pad_width+1
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
            if data[x,y] != 0:
                superpos[x,y,:] = False
                superpos[x,y,data[x,y]-1] = True


def collapse(superpos):
    print(np.argwhere(np.sum(superpos,axis=2) == 1))
    new_data = np.zeros((9,9),dtype='uint8')
    indices=np.argwhere(np.sum(superpos,axis=2) == 1)
    print(superpos[:3,:3])
    print(np.unique(superpos[:3,:3], axis=2, return_index=True, return_counts=True, return_inverse=True))
    return new_data

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
    
    table = UnicodeTable(9,9,1,0,1,1)
    for y in range(0,9):
        for x in range(0,9):
            if data[x][y] != 0:
                table[x,y] = data[x][y]
    print(table)

    superpos = np.ndarray((9,9,9),dtype='bool')
    data_to_superposition(data,superpos)
    collapse(superpos)


    


