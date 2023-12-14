import random


class cpu:
    def __init__(self) -> None:
        self.memory = [0]*4096 # max 4096
        self.gpio = [0]*16 # max 16 -> special registers
        self.display_buffer = [0]*32*64 # 64*32
        self.stack = [] # stack
        self.key_inputs = [0]*16 # key inputs
        self.fonts=[0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
                    0x20, 0x60, 0x20, 0x20, 0x70, # 1
                    0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
                    0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
                    0x90, 0x90, 0xF0, 0x10, 0x10, # 4
                    0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
                    0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
                    0xF0, 0x10, 0x20, 0x40, 0x40, # 7
                    0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
                    0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
                    0xF0, 0x90, 0xF0, 0x90, 0x90, # A
                    0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
                    0xF0, 0x80, 0x80, 0x80, 0xF0, # C
                    0xE0, 0x90, 0x90, 0x90, 0xE0, # D
                    0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
                    0xF0, 0x80, 0xF0, 0x80, 0x80  # F
                    ]
        self.pc = 0 # program counter
        self.opcode = 0 # current opcode
        self.index = 0 # index register
        self.delay_timer = 0 # delay timer
        self.sound_timer = 0 # sound timer
        # instruction functions
        self.vx = 0 # store register numbers here for op method access
        self.vy = 0
        self.update_display = False
        self.op2func={  0x0000: self._0XXX,
                        0x00e0: self._0XX0,
                        0x00ee: self._0XXE,
                        0x1000: self._1XXX,
                        0x2000: self._2XXX,
                        0x3000: self._3XXX,
                        0x4000: self._4XXX,
                        0x5000: self._5XXX,
                        0x6000: self._6XXX,
                        0x7000: self._7XXX,
                        0x8000: self._8XXX,
                        0x8000: self._8XX0,
                        0x8001: self._8XX1,
                        0x8002: self._8XX2,
                        0x8003: self._8XX3,
                        0x8004: self._8XX4,
                        0x8005: self._8XX5,
                        0x8006: self._8XX6,
                        0x8007: self._8XX7,
                        0x800E: self._8XXE,
                        0x9000: self._9XXX,
                        0xA000: self._AXXX,
                        0xB000: self._BXXX,
                        0xC000: self._CXXX,
                        0xD000: self._DXXX,
                        0xE000: self._EXXX,
                        0xE00E: self._EXXE,
                        0xE001: self._EXX1,
                        0xF000: self._FXXX,
                        0xF007: self._FX07,
                        0xF00A: self._FX0A,
                        0xF015: self._FX15,
                        0xF018: self._FX18,
                        0xF01E: self._FX1E,
                        0xF029: self._FX29,
                        0xF033: self._FX33,
                        0xF055: self._FX55,
                        0xF065: self._FX65
                    }
    def load_rom(self, rom_path):
        binary = open(rom_path, "rb").read()
        print(len(binary))
        # print(binary)
        for i in range(len(binary)):
            self.memory[i+0x200] = binary[i]
    
    def load_fonts(self):
        # load fonts into memory 80 char font set 
        for i in range(len(self.fonts)):
            self.memory[i] = self.fonts[i]
    
    def init_cpu(self):
        # self.clear()
        self.memory = [0]*4096 # max 4096
        self.gpio = [0]*16 # max 16
        self.display_buffer = [0]*64*32 # 64*32
        self.stack = []
        self.key_inputs = [0]*16  
        self.opcode = 0
        self.index = 0

        self.delay_timer = 0
        self.sound_timer = 0
        self.update_display = False
        
        self.pc = 0x200
        self.load_fonts()
    
    def cycle(self):
        # get opcode
        self.opcode = (self.memory[self.pc] <<8) | self.memory[self.pc+1]
        # inc program counter 
        self.pc+=2
        # parse opcode for args
        self.vx = (self.opcode & 0x0f00) >> 8
        self.vy = (self.opcode & 0x00f0) >> 4

        # extract operation
        extracted_op = self.opcode & 0xf000 
        try:
            self.op2func[extracted_op]()
        except KeyError:
            print(f"Unknown opcode: {hex(self.opcode)} or {hex(extracted_op)} at {hex(self.pc)}")
        except Exception as e:
            print(f"Unknown error: {e} at {hex(self.pc)}")

        
        # handle special timers
        if self.delay_timer > 0:
            self.delay_timer-=1
        if self.sound_timer > 0:
            self.sound_timer-=1
        
        

    def _0XXX(self):
        # 0x0NNN
        extracted_op = self.opcode & 0xf0ff
        try:
            self.op2func[extracted_op]()
        except:
            print(f"Unknown opcode: {hex(self.opcode)} at {hex(self.pc)} type 0")
        
    def _0XX0(self):
        # clear screen
        self.display_buffer = [0]*64*32
        self.update_display = True
    
    def _0XXE(self):
        # return from subroutine
        self.pc = self.stack.pop()
    
    def _1XXX(self):
        # jump to address
        self.pc = self.opcode & 0x0fff
    
    def _2XXX(self):
        # call subroutine
        self.stack.append(self.pc)
        self.pc = self.opcode & 0x0fff

    def _3XXX(self):
        # skip next instruction if Vx == NN
        if self.gpio[self.vx] == (self.opcode & 0x00ff):
            self.pc += 2
    
    def _4XXX(self):
        # skip next instruction if Vx != NN
        if self.gpio[self.vx] != (self.opcode & 0x00ff):
            self.pc += 2
    
    def _5XXX(self):
        # skip next instruction if Vx == Vy
        if self.gpio[self.vx] == self.gpio[self.vy]:
            self.pc += 2
    
    def _6XXX(self):
        # set Vx = NN
        self.gpio[self.vx] = self.opcode & 0x00ff

    def _7XXX(self):
        # set Vx = Vx + NN
        self.gpio[self.vx] += self.opcode & 0x00ff

    def _8XXX(self):
        # 0x8XYN
        extracted_op = self.opcode & 0xf00f
        try:
            self.op2func[extracted_op]()
        except:
            print(f"Unknown opcode: {hex(self.opcode)} at {hex(self.pc)} type 8")
    
    def _8XX0(self):
        # set Vx = Vy
        self.gpio[self.vx] = self.gpio[self.vy]
        self.gpio[self.vx] &= 0xff

    def _8XX1(self):
        # set Vx = Vx OR Vy
        self.gpio[self.vx] |= self.gpio[self.vy]
        self.gpio[self.vx] &= 0xff

    def _8XX2(self):
        # set Vx = Vx AND Vy
        self.gpio[self.vx] &= self.gpio[self.vy]
        self.gpio[self.vx] &= 0xff

    def _8XX3(self):
        # set Vx = Vx XOR Vy
        self.gpio[self.vx] ^= self.gpio[self.vy]
        self.gpio[self.vx] &= 0xff

    def _8XX4(self):
        # set Vx = Vx + Vy, set VF = carry
        if self.gpio[self.vx] + self.gpio[self.vy] > 0xff:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.gpio[self.vx] += self.gpio[self.vy]
        self.gpio[self.vx] &= 0xff
    
    def _8XX5(self):
        # set Vx = Vx - Vy, set VF = NOT borrow
        if self.gpio[self.vx] > self.gpio[self.vy]:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.gpio[self.vx] -= self.gpio[self.vy]
        self.gpio[self.vx] &= 0xff

    def _8XX6(self):
        # set Vx = Vx >> 1 (shift right), set VF = LSB of Vx before shift
        self.gpio[0xf] = self.gpio[self.vx] & 0x1
        self.gpio[self.vx] >>= 1
        self.gpio[self.vx] &= 0xff

    def _8XX7(self):
        # set Vx = Vy - Vx, set VF = NOT borrow
        if self.gpio[self.vy] > self.gpio[self.vx]:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.gpio[self.vx] = self.gpio[self.vy] - self.gpio[self.vx]
        self.gpio[self.vx] &= 0xff

    def _8XXE(self):
        # set Vx = Vx << 1 (shift left), set VF = MSB of Vx before shift
        self.gpio[0xf] = self.gpio[self.vx] & 0x80
        self.gpio[self.vx] <<= 1
        self.gpio[self.vx] &= 0xff

    def _9XXX(self):
        # skip next instruction if Vx != Vy
        if self.gpio[self.vx] != self.gpio[self.vy]:
            self.pc += 2

    def _AXXX(self):
        # set I = NNN
        self.index = self.opcode & 0x0fff

    def _BXXX(self):
        # jump to address NNN + V0
        self.pc = (self.opcode & 0x0fff) + self.gpio[0]

    def _CXXX(self):
        # set Vx = random byte AND NN
        self.gpio[self.vx] = random.randint(0, 0xff) & (self.opcode & 0x00ff)
        self.gpio[self.vx] &= 0xff

    def _DXXX(self):
        # display N-byte sprite starting at memory location I at (Vx, Vy), set VF = collision
        self.gpio[0xf] = 0
        x = self.gpio[self.vx] & 0xff
        y = self.gpio[self.vy] & 0xff
        height = self.opcode & 0x000f
        for yline in range(height): # 0 to height
            pixel = self.memory[self.index + yline]
            for xline in range(8): # 0 to width (8)
                if (pixel & (0x80 >> xline)) != 0: # check if pixel is set 
                    if self.display_buffer[(x + xline + ((y + yline) * 64))] == 1: # check if pixel is already set
                        self.gpio[0xf] = 1
                    self.display_buffer[x + xline + ((y + yline) * 64)] ^= 1
        self.update_display = True

    def _EXXX(self):
        # 0xEXXX
        extracted_op = self.opcode & 0xf00f
        try:
            self.op2func[extracted_op]()
        except:
            print(f"Unknown opcode: {hex(self.opcode)} at {hex(self.pc)} type E")

    def _EXXE(self):
        # skip next instruction if key with the value of Vx is pressed
        if self.key_inputs[self.gpio[self.vx]] != 0:
            self.pc += 2

    def _EXX1(self):
        # skip next instruction if key with the value of Vx is not pressed
        if self.key_inputs[self.gpio[self.vx]] == 0:
            self.pc += 2

    def _FXXX(self):
        # 0xFXXX
        extracted_op = self.opcode & 0xf0ff
        try:
            self.op2func[extracted_op]()
        except:
            print(f"Unknown opcode: {hex(self.opcode)} at {hex(self.pc)} type F")

    def _FX07(self):
        # set Vx = delay timer value
        self.gpio[self.vx] = self.delay_timer

    def _FX0A(self):
        # wait for a key press, store the value of the key in Vx
        key_pressed = False
        for i in range(len(self.key_inputs)): # 0 to 15
            if self.key_inputs[i] != 0: # check if key is pressed
                self.gpio[self.vx] = i
                key_pressed = True
        if not key_pressed:
            self.pc -= 2

    def _FX15(self):
        # set delay timer = Vx
        self.delay_timer = self.gpio[self.vx]

    def _FX18(self):
        # set sound timer = Vx
        self.sound_timer = self.gpio[self.vx]

    def _FX1E(self):
        # set I = I + Vx, set VF = carry
        if self.index + self.gpio[self.vx] > 0xfff:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.index += self.gpio[self.vx]
        self.index &= 0xfff

    def _FX29(self):
        # set I = location of sprite for digit Vx
        self.index = (self.gpio[self.vx] * 5) & 0xfff
    
    def _FX33(self):
        # store BCD representation of Vx in memory locations I, I+1, and I+2
        self.memory[self.index] = self.gpio[self.vx] // 100
        self.memory[self.index+1] = (self.gpio[self.vx] % 100) // 10
        self.memory[self.index+2] = self.gpio[self.vx] % 10

    def _FX55(self):
        # store registers V0 through Vx in memory starting at location I
        for i in range(self.vx+1):
            self.memory[self.index+i] = self.gpio[i]
        self.index += self.vx + 1

    def _FX65(self):
        # read registers V0 through Vx from memory starting at location I
        for i in range(self.vx+1):
            self.gpio[i] = self.memory[self.index+i]
        self.index += self.vx + 1



