import re
import struct
import tkinter as tk
from tkinter import filedialog, messagebox
class parse_101(object): #报文解析
    def __init__(self, message):
        self.message_raw = message
        self.outtext = ""
        self.message_list = self.message_extract()
        self.message_format = ""
        self.lenth ={"information_body_address":2,
                    "single_point_information":1,
                    "timestamp":7,
                    "quality":1,
                    "floating-point measurement":4,
                    "APCI":13,
                    "type_identifier_locate":7,}
        try:
            for self.message_format in self.message_list:
                type_identifier = self.message_format[self.lenth["type_identifier_locate"]]
                type_result = self.message_format[self.lenth["type_identifier_locate"]+2]
                if type_identifier == "01":
                    if type_result == "03":
                        self.outtext += "【↑】单点遥信报文:\n"
                        #self.outtext += str(self.message_format).replace("', '"," ")
                        self.YX_parse(0,0,0)
                    if type_result == "14":
                        self.outtext += "【↑】遥信响应总召报文:\n"
                elif type_identifier == "1E" or type_identifier == "1e":
                    self.outtext += "【↑】单点遥信SOE报文:\n"
                    self.YX_parse(0,0,1)
                elif type_identifier == "0D" or type_identifier == "0d":
                    if type_result == "03":
                        self.outtext += "【↑】遥测报文:\n"
                        self.YC_parse(0,0)
                    if type_result == "14":
                        self.outtext += "【↑】遥测响应总召报文:\n"
                elif type_identifier == "2A" or type_identifier == "2a":
                    self.outtext += "【↑】故障事件报文:\n"
                    self.GZSJ_parse()
                elif type_identifier == "CF" or type_identifier == "cf":
                    self.outtext += "【↑】电能量报文:\n"
                elif type_identifier == "CE" or type_identifier == "ce":
                    self.outtext += "【↑】电能量响应总召报文:\n"
                elif type_identifier == "64":
                    self.outtext += "【↑】总召唤报文:\n"
                elif type_identifier == "46":
                    self.outtext += "【↑】初始化结束报文:\n"
                elif type_identifier == "65":
                    self.outtext += "【↑】电能量召唤报文:\n"
                else:
                    self.outtext += f"【↑】暂不支持解析:（类型标识{type_identifier}）\n"
        except:
            pass
        print(self.outtext)
        with open("解析结果.txt","a",encoding="utf-8") as f:
            f.write(self.message_raw+"\n")
            f.write(self.outtext)
    def message_extract(self): #报文提取
        pattern = r'(68(?:\s+[0-9A-Fa-f]+)*\s+16)'
        print(self.message_raw)
        match = re.search(pattern, self.message_raw)
        if match:
            target_massage = match.group(1)
            format_massage = target_massage.split(" ")
            log_list = []
            for i in range(len(format_massage)):
                try:
                    if (format_massage[i] == "68") and (format_massage[i+1] == format_massage[i+2]):
                        if format_massage[i+3] == "68":
                            lenth = int(format_massage[i+1],16)
                            log = format_massage[i:i+lenth+6]
                            log_list += [log]
                except:pass
            return log_list #['68', '18', '18', '16']
        else:
            print("No target message found in the raw message.")
        
    def data_reverse(self,fotmat_massage,start,end): #数据计算,将指定位置报文翻转并转为str(无空格)，用于进一步计算数据,start和end为起始位和终止位
        start = start-1
        end = end
        data = fotmat_massage[start:end]
        data.reverse()
        hex_str = ''.join(data)
        return hex_str 
    
    def parse_101_soe_timestamp(self,soe_hex_str):
        if len(soe_hex_str) != 14:
            raise ValueError("SOE时标十六进制字符串必须为14位，当前输入长度：{}".format(len(soe_hex_str)))
        soe_bytes = bytes.fromhex(soe_hex_str)  # 转换后为7字节bytes对象，如b'2\x01\n\x08\x1e\n\x18'
        ms_low = soe_bytes[6]    # 第1字节：毫秒低位
        ms_high = soe_bytes[5]   # 第2字节：毫秒高位
        minute = soe_bytes[4]    # 第3字节：分钟（0-59）
        hour = soe_bytes[3]      # 第4字节：小时（0-23）
        day = soe_bytes[2] % 32       # 第5字节：日（1-31）
        month = soe_bytes[1]    # 第6字节：月（1-12）
        year = soe_bytes[0]      # 第7字节：年（后两位，如24→2024）
        total_ms = (ms_high * 256 + ms_low)/1000
        full_year = 2000 + year  # 转换为4位年份（默认21世纪，可按需调整）
        time_str = f"{full_year:04d}-{month:02d}-{day:02d} " \
                f"{hour:02d}:{minute:02d}"
        time_str = time_str+":"+str(total_ms)
        return time_str

    def YC_parse(self,YC_num=0,is_GZSJ=0,start_adress=0): #遥测解析
        def YC_caculate(data):
            data = int(data, 16)
            byte_data = data.to_bytes(4, byteorder='big')
            float_value = struct.unpack('>f', byte_data)[0] 
            return float_value
        if YC_num == 0:
            YC_num = int(self.message_format[self.lenth["type_identifier_locate"]+1],16)
        for i in range(YC_num):
            if is_GZSJ == 0:
                start_adress = 1+self.lenth["APCI"]+(self.lenth["information_body_address"]+self.lenth["floating-point measurement"]+self.lenth["quality"])*(i)
            if is_GZSJ == 1:
                start_adress = start_adress + (self.lenth["information_body_address"]+self.lenth["floating-point measurement"])
            information_body_address = self.data_reverse(self.message_format,start_adress,start_adress+1)
            data =  YC_caculate(self.data_reverse(self.message_format,start_adress+2,start_adress+5))
            self.outtext += f"遥测信息体地址：{information_body_address}(点号{int(information_body_address,16)-16384}),值：{data}\n"

    def YX_parse(self,YX_num=0,is_GZSJ=0,is_SOE=0): #遥信解析
        if YX_num == 0:
            YX_num = int(self.message_format[self.lenth["type_identifier_locate"]+1],16)
        for i in range(YX_num):
            if is_SOE == 0:
                loop_address = self.lenth["information_body_address"]+self.lenth["single_point_information"]
            if is_SOE == 1:    
                loop_address = self.lenth["information_body_address"]+self.lenth["single_point_information"]+self.lenth["timestamp"]
            start_adress = 1+self.lenth["APCI"]+(loop_address)*(i)
            if is_GZSJ == 1:
                start_adress = 3+self.lenth["APCI"]+(loop_address)*(i)
            information_body_address = self.data_reverse(self.message_format,start_adress,start_adress+1)
            data = self.data_reverse(self.message_format,start_adress+2,start_adress+2)
            if is_SOE == 1:    
                timestamp = self.data_reverse(self.message_format,start_adress+3,start_adress+9)
                timestamp = self.parse_101_soe_timestamp(timestamp)
                self.outtext += f"遥信信息体地址：{information_body_address}(点号{int(information_body_address,16)}),值：{data},时间：{timestamp}\n"
            else:
                self.outtext += f"遥信信息体地址：{information_body_address}(点号{int(information_body_address,16)}),值：{data}\n"

    def GZSJ_parse(self): #故障事件解析
        YX_num = int(self.message_format[self.lenth["APCI"]],16)
        self.YX_parse(YX_num,1,1)
        YC_num = int(self.message_format[self.lenth["APCI"]+10*YX_num+2],16)
        adress = self.lenth["APCI"]+10*YX_num+2+2+1 #（2+2为遥测遥信的类型标识及可变结构限定词，+1为data_reverse函数的补偿）
        self.YC_parse(YC_num,1,adress)
        pass

class FileProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文件处理工具")
        self.root.geometry("400x200")  # 窗口大小：宽400，高200
        
        # 存储选中的文件路径
        self.selected_file = None
        
        # 创建UI组件
        self.create_widgets()
    
    def create_widgets(self):
        # 标签：显示选中的文件路径
        self.file_label = tk.Label(
            self.root, 
            text="未选择文件", 
            wraplength=350,  # 文本超过350像素自动换行
            justify="left"
        )
        self.file_label.pack(pady=20)
        
        # 按钮框架：放置选择文件和执行按钮
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        # 选择文件按钮
        self.select_btn = tk.Button(
            button_frame,
            text="选择文件",
            command=self.select_file,
            width=15
        )
        self.select_btn.grid(row=0, column=0, padx=10)
        
        # 执行按钮
        self.execute_btn = tk.Button(
            button_frame,
            text="执行",
            command=self.execute,
            width=15
        )
        self.execute_btn.grid(row=0, column=1, padx=10)
    
    def select_file(self):
        """打开文件选择对话框并更新显示"""
        file_path = filedialog.askopenfilename(
            title="选择文件",
            filetypes=[("所有文件", "*.*")]  # 可根据需要限制文件类型，如[("文本文件", "*.txt")]
        )
        
        if file_path:  # 如果用户选择了文件（未取消）
            self.selected_file = file_path
            self.file_label.config(text=f"选中文件：{file_path}")
    
    def execute(self):
        if not self.selected_file:
            messagebox.showwarning("提示", "请先选择文件！")
        else:
            messagebox.showinfo("执行中", "点击确定开始执行")
            with open("解析结果.txt","w",encoding="utf-8") as f:
                f.write("")
            with open(f"{self.selected_file}","r",encoding="utf-8") as f:
                for line in f: 
                    line = line.strip()
                    AAA = parse_101(line)
            messagebox.showinfo("执行结果", "执行完成，结果保存至本目录“解析结果.txt”")
if __name__ == "__main__":
    root = tk.Tk()
    app = FileProcessorApp(root)
    root.mainloop()
