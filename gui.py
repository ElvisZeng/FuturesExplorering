"""
期货数据管理系统图形化界面
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from tkcalendar import DateEntry
from ttkthemes import ThemedTk

from data_manager import data_manager
from database import db_manager
from config import GUI_CONFIG, EXCHANGES

class FuturesDataGUI:
    """期货数据管理系统GUI"""
    
    def __init__(self):
        self.root = ThemedTk(theme="arc")
        self.root.title(GUI_CONFIG['window_title'])
        self.root.geometry(GUI_CONFIG['window_size'])
        
        # 初始化变量
        self.current_data = pd.DataFrame()
        self.chart_frame = None
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 注册数据管理器回调
        data_manager.add_update_callback(self.update_status)
        
        # 初始化状态
        self.update_data_summary()
    
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        
        # 配置按钮样式
        style.configure("Action.TButton", padding=(10, 5))
        style.configure("Small.TButton", padding=(5, 2))
        
        # 配置标签样式
        style.configure("Title.TLabel", font=("Arial", 12, "bold"))
        style.configure("Status.TLabel", font=("Arial", 9))
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建笔记本控件（标签页）
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个标签页
        self.create_data_management_tab()
        self.create_chart_tab()
        self.create_settings_tab()
        self.create_log_tab()
        
        # 创建状态栏
        self.create_status_bar(main_frame)
    
    def create_data_management_tab(self):
        """创建数据管理标签页"""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="数据管理")
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(data_frame, text="数据操作", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 数据下载区域
        download_frame = ttk.LabelFrame(control_frame, text="数据下载")
        download_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 日期选择
        ttk.Label(download_frame, text="开始日期:").pack(anchor=tk.W)
        self.start_date_entry = DateEntry(download_frame, width=12, 
                                         background='darkblue',
                                         foreground='white', 
                                         borderwidth=2,
                                         date_pattern='y-mm-dd')
        self.start_date_entry.pack(pady=(0, 5))
        self.start_date_entry.set_date(datetime.now() - timedelta(days=30))
        
        ttk.Label(download_frame, text="结束日期:").pack(anchor=tk.W)
        self.end_date_entry = DateEntry(download_frame, width=12,
                                       background='darkblue',
                                       foreground='white',
                                       borderwidth=2,
                                       date_pattern='y-mm-dd')
        self.end_date_entry.pack(pady=(0, 5))
        
        # 交易所选择
        ttk.Label(download_frame, text="交易所:").pack(anchor=tk.W)
        self.exchange_var = tk.StringVar()
        exchange_combo = ttk.Combobox(download_frame, textvariable=self.exchange_var,
                                     values=list(EXCHANGES.keys()) + ["全部"])
        exchange_combo.pack(pady=(0, 5))
        exchange_combo.set("全部")
        
        # 下载按钮
        ttk.Button(download_frame, text="下载数据", 
                  command=self.download_data,
                  style="Action.TButton").pack(pady=5)
        
        # CSV导入区域
        csv_frame = ttk.LabelFrame(control_frame, text="CSV导入")
        csv_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(csv_frame, text="选择CSV文件",
                  command=self.import_csv_file,
                  style="Action.TButton").pack(pady=5)
        
        # 数据更新区域
        update_frame = ttk.LabelFrame(control_frame, text="数据更新")
        update_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(update_frame, text="更新当日数据",
                  command=self.update_daily_data,
                  style="Action.TButton").pack(pady=2)
        
        ttk.Button(update_frame, text="启动定时更新",
                  command=self.start_scheduled_update,
                  style="Small.TButton").pack(pady=2)
        
        ttk.Button(update_frame, text="停止定时更新",
                  command=self.stop_scheduled_update,
                  style="Small.TButton").pack(pady=2)
        
        # 数据管理区域
        manage_frame = ttk.LabelFrame(control_frame, text="数据管理")
        manage_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(manage_frame, text="导出数据",
                  command=self.export_data,
                  style="Small.TButton").pack(pady=2)
        
        ttk.Button(manage_frame, text="清理旧数据",
                  command=self.cleanup_old_data,
                  style="Small.TButton").pack(pady=2)
        
        # 右侧数据显示区域
        display_frame = ttk.LabelFrame(data_frame, text="数据概览", padding=10)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 数据概要显示
        self.summary_text = scrolledtext.ScrolledText(display_frame, height=15, width=50)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # 刷新按钮
        ttk.Button(display_frame, text="刷新概要",
                  command=self.update_data_summary,
                  style="Small.TButton").pack(pady=(10, 0))
    
    def create_chart_tab(self):
        """创建图表标签页"""
        chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(chart_frame, text="数据图表")
        
        # 左侧控制面板
        chart_control_frame = ttk.LabelFrame(chart_frame, text="图表控制", padding=10)
        chart_control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 产品选择
        ttk.Label(chart_control_frame, text="交易所:").pack(anchor=tk.W)
        self.chart_exchange_var = tk.StringVar()
        chart_exchange_combo = ttk.Combobox(chart_control_frame, 
                                           textvariable=self.chart_exchange_var,
                                           width=15)
        chart_exchange_combo.pack(pady=(0, 5))
        chart_exchange_combo.bind('<<ComboboxSelected>>', self.on_exchange_selected)
        
        ttk.Label(chart_control_frame, text="品种:").pack(anchor=tk.W)
        self.chart_product_var = tk.StringVar()
        self.chart_product_combo = ttk.Combobox(chart_control_frame,
                                               textvariable=self.chart_product_var,
                                               width=15)
        self.chart_product_combo.pack(pady=(0, 5))
        
        # 合约类型选择
        ttk.Label(chart_control_frame, text="合约类型:").pack(anchor=tk.W)
        self.contract_type_var = tk.StringVar()
        contract_type_combo = ttk.Combobox(chart_control_frame,
                                          textvariable=self.contract_type_var,
                                          values=["主力合约", "加权合约"],
                                          width=15)
        contract_type_combo.pack(pady=(0, 5))
        contract_type_combo.set("主力合约")
        
        # 日期范围选择
        ttk.Label(chart_control_frame, text="开始日期:").pack(anchor=tk.W)
        self.chart_start_date = DateEntry(chart_control_frame, width=12,
                                         background='darkblue',
                                         foreground='white',
                                         borderwidth=2,
                                         date_pattern='y-mm-dd')
        self.chart_start_date.pack(pady=(0, 5))
        self.chart_start_date.set_date(datetime.now() - timedelta(days=90))
        
        ttk.Label(chart_control_frame, text="结束日期:").pack(anchor=tk.W)
        self.chart_end_date = DateEntry(chart_control_frame, width=12,
                                       background='darkblue',
                                       foreground='white',
                                       borderwidth=2,
                                       date_pattern='y-mm-dd')
        self.chart_end_date.pack(pady=(0, 5))
        
        # 图表类型选择
        ttk.Label(chart_control_frame, text="图表类型:").pack(anchor=tk.W)
        self.chart_type_var = tk.StringVar()
        chart_type_combo = ttk.Combobox(chart_control_frame,
                                       textvariable=self.chart_type_var,
                                       values=["K线图", "收盘价线图", "成交量柱状图"],
                                       width=15)
        chart_type_combo.pack(pady=(0, 5))
        chart_type_combo.set("K线图")
        
        # 显示图表按钮
        ttk.Button(chart_control_frame, text="显示图表",
                  command=self.show_chart,
                  style="Action.TButton").pack(pady=10)
        
        # 右侧图表显示区域
        self.chart_display_frame = ttk.Frame(chart_frame)
        self.chart_display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 初始化图表区域
        self.init_chart_area()
        
        # 初始化交易所和产品列表
        self.update_chart_options()
    
    def create_settings_tab(self):
        """创建设置标签页"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="系统设置")
        
        # 数据库设置
        db_frame = ttk.LabelFrame(settings_frame, text="数据库设置", padding=10)
        db_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 数据库连接状态
        self.db_status_label = ttk.Label(db_frame, text="数据库状态: 检查中...",
                                        style="Status.TLabel")
        self.db_status_label.pack(anchor=tk.W)
        
        ttk.Button(db_frame, text="测试数据库连接",
                  command=self.test_database_connection,
                  style="Small.TButton").pack(anchor=tk.W, pady=(5, 0))
        
        # 定时更新设置
        schedule_frame = ttk.LabelFrame(settings_frame, text="定时更新设置", padding=10)
        schedule_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(schedule_frame, text="每日更新时间:").pack(anchor=tk.W)
        self.update_time_var = tk.StringVar(value="18:00")
        update_time_entry = ttk.Entry(schedule_frame, textvariable=self.update_time_var, width=10)
        update_time_entry.pack(anchor=tk.W, pady=(0, 5))
        
        # 基本面数据导入
        fundamentals_frame = ttk.LabelFrame(settings_frame, text="基本面数据导入", padding=10)
        fundamentals_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(fundamentals_frame, text="选择基本面数据文件:").pack(anchor=tk.W)
        ttk.Button(fundamentals_frame, text="导入基本面数据",
                  command=self.import_fundamentals_data,
                  style="Action.TButton").pack(anchor=tk.W, pady=(5, 0))
    
    def create_log_tab(self):
        """创建日志标签页"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="系统日志")
        
        # 日志显示区域
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 清除日志按钮
        ttk.Button(log_frame, text="清除日志",
                  command=self.clear_log,
                  style="Small.TButton").pack(pady=(0, 10))
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪", style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
    
    def init_chart_area(self):
        """初始化图表区域"""
        # 创建matplotlib图形
        self.fig = Figure(figsize=(10, 8), dpi=100)
        self.chart_canvas = FigureCanvasTkAgg(self.fig, self.chart_display_frame)
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加默认提示
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, '请选择数据并点击"显示图表"', 
               horizontalalignment='center', verticalalignment='center',
               transform=ax.transAxes, fontsize=14)
        ax.set_xticks([])
        ax.set_yticks([])
        self.chart_canvas.draw()
    
    def update_status(self, message: str):
        """更新状态信息"""
        self.status_label.config(text=message)
        self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_progress(self):
        """开始进度条"""
        self.progress_bar.start()
    
    def stop_progress(self):
        """停止进度条"""
        self.progress_bar.stop()
    
    def download_data(self):
        """下载数据"""
        def download_thread():
            try:
                self.start_progress()
                start_date = self.start_date_entry.get()
                end_date = self.end_date_entry.get()
                
                exchange = self.exchange_var.get()
                exchanges = None if exchange == "全部" else [exchange]
                
                # 下载数据
                raw_data = data_manager.download_historical_data(start_date, end_date, exchanges)
                
                if raw_data:
                    # 处理并导入数据
                    data_manager.process_and_import_data(raw_data)
                    self.root.after(0, self.update_data_summary)
                
            except Exception as e:
                self.update_status(f"下载数据失败: {e}")
            finally:
                self.stop_progress()
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def import_csv_file(self):
        """导入CSV文件"""
        file_path = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            def import_thread():
                try:
                    self.start_progress()
                    success = data_manager.import_csv_to_database(file_path)
                    if success:
                        self.root.after(0, self.update_data_summary)
                except Exception as e:
                    self.update_status(f"导入CSV失败: {e}")
                finally:
                    self.stop_progress()
            
            threading.Thread(target=import_thread, daemon=True).start()
    
    def update_daily_data(self):
        """更新当日数据"""
        def update_thread():
            try:
                self.start_progress()
                data_manager.update_daily_data()
                self.root.after(0, self.update_data_summary)
            except Exception as e:
                self.update_status(f"更新当日数据失败: {e}")
            finally:
                self.stop_progress()
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def start_scheduled_update(self):
        """启动定时更新"""
        update_time = self.update_time_var.get()
        data_manager.start_scheduled_updates(update_time)
    
    def stop_scheduled_update(self):
        """停止定时更新"""
        data_manager.stop_scheduled_updates()
    
    def export_data(self):
        """导出数据"""
        # 这里可以添加导出对话框，选择条件
        file_path = filedialog.asksaveasfilename(
            title="保存数据文件",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            def export_thread():
                try:
                    self.start_progress()
                    result = data_manager.export_data_to_csv(filename=file_path)
                    if result:
                        self.update_status(f"数据已导出: {result}")
                except Exception as e:
                    self.update_status(f"导出数据失败: {e}")
                finally:
                    self.stop_progress()
            
            threading.Thread(target=export_thread, daemon=True).start()
    
    def cleanup_old_data(self):
        """清理旧数据"""
        result = messagebox.askyesno("确认", "确定要清理365天前的旧数据吗？")
        if result:
            def cleanup_thread():
                try:
                    self.start_progress()
                    data_manager.cleanup_old_data()
                    self.root.after(0, self.update_data_summary)
                except Exception as e:
                    self.update_status(f"清理数据失败: {e}")
                finally:
                    self.stop_progress()
            
            threading.Thread(target=cleanup_thread, daemon=True).start()
    
    def update_data_summary(self):
        """更新数据概要"""
        def summary_thread():
            try:
                summary = data_manager.get_data_summary()
                
                summary_text = "=== 数据库概要信息 ===\n\n"
                summary_text += f"数据库连接状态: {'正常' if summary['database_status'] else '异常'}\n"
                
                if summary['database_status']:
                    summary_text += f"总记录数: {summary.get('total_records', 0):,}\n"
                    summary_text += f"可用交易所: {', '.join(summary.get('available_exchanges', []))}\n"
                    summary_text += f"可用品种数: {len(summary.get('available_products', []))}\n"
                    
                    if summary.get('date_range'):
                        summary_text += f"数据日期范围: {summary['date_range']['start_date']} 至 {summary['date_range']['end_date']}\n"
                    
                    summary_text += "\n=== 可用品种列表 ===\n"
                    products = summary.get('available_products', [])
                    for i, product in enumerate(products):
                        if i % 10 == 0:
                            summary_text += "\n"
                        summary_text += f"{product:>6} "
                else:
                    summary_text += f"错误信息: {summary.get('error', '未知错误')}\n"
                
                def update_ui():
                    self.summary_text.delete(1.0, tk.END)
                    self.summary_text.insert(1.0, summary_text)
                    
                    # 更新数据库状态
                    status_text = "数据库状态: " + ("正常" if summary['database_status'] else "异常")
                    self.db_status_label.config(text=status_text)
                
                self.root.after(0, update_ui)
                
            except Exception as e:
                self.update_status(f"获取数据概要失败: {e}")
        
        threading.Thread(target=summary_thread, daemon=True).start()
    
    def update_chart_options(self):
        """更新图表选项"""
        def update_thread():
            try:
                summary = data_manager.get_data_summary()
                if summary['database_status']:
                    exchanges = summary.get('available_exchanges', [])
                    
                    def update_ui():
                        self.chart_exchange_var.set('')
                        self.chart_exchange_combo['values'] = exchanges
                        if exchanges:
                            self.chart_exchange_var.set(exchanges[0])
                            self.on_exchange_selected()
                    
                    self.root.after(0, update_ui)
            except Exception as e:
                self.update_status(f"更新图表选项失败: {e}")
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def on_exchange_selected(self, event=None):
        """交易所选择事件"""
        exchange = self.chart_exchange_var.get()
        if exchange:
            products = db_manager.get_available_products(exchange)
            self.chart_product_combo['values'] = products
            if products:
                self.chart_product_var.set(products[0])
    
    def show_chart(self):
        """显示图表"""
        def chart_thread():
            try:
                self.start_progress()
                
                exchange = self.chart_exchange_var.get()
                product = self.chart_product_var.get()
                contract_type = "main" if self.contract_type_var.get() == "主力合约" else "weighted"
                start_date = self.chart_start_date.get()
                end_date = self.chart_end_date.get()
                chart_type = self.chart_type_var.get()
                
                if not all([exchange, product]):
                    self.update_status("请选择交易所和品种")
                    return
                
                # 获取连续合约数据
                data = db_manager.get_continuous_contract_data(
                    exchange=exchange,
                    product_code=product,
                    contract_type=contract_type,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if data.empty:
                    self.update_status("没有找到符合条件的数据")
                    return
                
                # 在主线程中更新图表
                self.root.after(0, lambda: self.update_chart(data, chart_type, exchange, product))
                
            except Exception as e:
                self.update_status(f"显示图表失败: {e}")
            finally:
                self.stop_progress()
        
        threading.Thread(target=chart_thread, daemon=True).start()
    
    def update_chart(self, data: pd.DataFrame, chart_type: str, exchange: str, product: str):
        """更新图表显示"""
        self.fig.clear()
        
        if chart_type == "K线图":
            self.plot_candlestick(data, exchange, product)
        elif chart_type == "收盘价线图":
            self.plot_line_chart(data, exchange, product)
        elif chart_type == "成交量柱状图":
            self.plot_volume_chart(data, exchange, product)
        
        self.chart_canvas.draw()
    
    def plot_candlestick(self, data: pd.DataFrame, exchange: str, product: str):
        """绘制K线图"""
        ax1 = self.fig.add_subplot(211)
        ax2 = self.fig.add_subplot(212)
        
        # 转换日期
        data['trade_date'] = pd.to_datetime(data['trade_date'])
        data = data.sort_values('trade_date')
        
        # 绘制K线图（简化版）
        for idx, row in data.iterrows():
            x = row['trade_date']
            open_price = row['open_price']
            high_price = row['high_price']
            low_price = row['low_price']
            close_price = row['close_price']
            
            # 确定颜色
            color = 'red' if close_price >= open_price else 'green'
            
            # 绘制高低线
            ax1.plot([x, x], [low_price, high_price], color='black', linewidth=1)
            
            # 绘制实体
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            
            ax1.bar(x, body_height, bottom=body_bottom, color=color, alpha=0.8, width=1)
        
        ax1.set_title(f'{exchange}-{product} K线图')
        ax1.set_ylabel('价格')
        ax1.grid(True, alpha=0.3)
        
        # 绘制成交量
        ax2.bar(data['trade_date'], data['volume'], alpha=0.7, color='blue')
        ax2.set_title('成交量')
        ax2.set_ylabel('成交量')
        ax2.set_xlabel('日期')
        ax2.grid(True, alpha=0.3)
        
        # 格式化日期轴
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        self.fig.tight_layout()
    
    def plot_line_chart(self, data: pd.DataFrame, exchange: str, product: str):
        """绘制收盘价线图"""
        ax = self.fig.add_subplot(111)
        
        data['trade_date'] = pd.to_datetime(data['trade_date'])
        data = data.sort_values('trade_date')
        
        ax.plot(data['trade_date'], data['close_price'], linewidth=2, color='blue')
        ax.set_title(f'{exchange}-{product} 收盘价走势')
        ax.set_ylabel('收盘价')
        ax.set_xlabel('日期')
        ax.grid(True, alpha=0.3)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        self.fig.tight_layout()
    
    def plot_volume_chart(self, data: pd.DataFrame, exchange: str, product: str):
        """绘制成交量柱状图"""
        ax = self.fig.add_subplot(111)
        
        data['trade_date'] = pd.to_datetime(data['trade_date'])
        data = data.sort_values('trade_date')
        
        ax.bar(data['trade_date'], data['volume'], alpha=0.7, color='green')
        ax.set_title(f'{exchange}-{product} 成交量')
        ax.set_ylabel('成交量')
        ax.set_xlabel('日期')
        ax.grid(True, alpha=0.3)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        self.fig.tight_layout()
    
    def test_database_connection(self):
        """测试数据库连接"""
        def test_thread():
            try:
                self.start_progress()
                success = db_manager.check_connection()
                status_text = "数据库状态: " + ("连接正常" if success else "连接失败")
                
                def update_ui():
                    self.db_status_label.config(text=status_text)
                    self.update_status("数据库连接测试完成")
                
                self.root.after(0, update_ui)
                
            except Exception as e:
                self.update_status(f"数据库连接测试失败: {e}")
            finally:
                self.stop_progress()
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def import_fundamentals_data(self):
        """导入基本面数据"""
        file_path = filedialog.askopenfilename(
            title="选择基本面数据文件",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if file_path:
            def import_thread():
                try:
                    self.start_progress()
                    
                    # 读取文件
                    if file_path.endswith('.csv'):
                        data = pd.read_csv(file_path, encoding='utf-8-sig')
                    elif file_path.endswith('.xlsx'):
                        data = pd.read_excel(file_path)
                    else:
                        raise ValueError("不支持的文件格式")
                    
                    success = data_manager.import_fundamentals_data(data)
                    if success:
                        self.update_status("基本面数据导入成功")
                    
                except Exception as e:
                    self.update_status(f"导入基本面数据失败: {e}")
                finally:
                    self.stop_progress()
            
            threading.Thread(target=import_thread, daemon=True).start()
    
    def clear_log(self):
        """清除日志"""
        self.log_text.delete(1.0, tk.END)
    
    def run(self):
        """运行程序"""
        try:
            self.root.mainloop()
        finally:
            # 清理资源
            data_manager.stop_scheduled_updates()
            db_manager.close_all_connections()

# 主程序入口
if __name__ == "__main__":
    app = FuturesDataGUI()
    app.run()