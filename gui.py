"""
期货数据管理系统图形化界面
"""
import tkinter as tk
import logging
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
from technical_indicators import tech_indicators
from trading_signals import signal_generator
from backtest_engine import backtest_engine
from data_upload import data_uploader
from custom_indicators import custom_indicator_builder
from live_trading_interface import live_trading_manager

class FuturesDataGUI:
    """期货数据管理系统GUI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.status_label = None #避免未初始化
        self.root = ThemedTk(theme="arc")
        self.root.title(GUI_CONFIG['window_title'])
        self.root.geometry(GUI_CONFIG['window_size'])
        
        
        # 初始化变量
        self.current_data = pd.DataFrame()
        self.chart_frame = None
            self.create_widgets()
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 注册数据管理器回调
        data_manager.add_update_callback(self.update_status)
        
        # 初始化分析和回测页面选项
        self.init_analysis_options()
        self.init_backtest_options()
        
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
        self.create_analysis_tab()
        self.create_backtest_tab()
        self.create_live_trading_tab()
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
    
    def init_analysis_options(self):
        """初始化分析页面选项"""
        try:
            exchanges = list(EXCHANGES.keys())
            self.analysis_exchange_combo['values'] = exchanges
            self.analysis_product_combo['values'] = []
            
            if exchanges:
                self.analysis_exchange_var.set(exchanges[0])
                self.on_analysis_exchange_selected()
        except Exception as e:
            self.logger.error(f"初始化分析选项失败: {e}")
    
    def init_backtest_options(self):
        """初始化回测页面选项"""
        try:
            exchanges = list(EXCHANGES.keys())
            self.backtest_exchange_combo['values'] = exchanges
            self.backtest_product_combo['values'] = []
            
            if exchanges:
                self.backtest_exchange_var.set(exchanges[0])
                self.on_backtest_exchange_selected()
        except Exception as e:
            self.logger.error(f"初始化回测选项失败: {e}")
    
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
        
        # 历史数据上传
        upload_frame = ttk.LabelFrame(settings_frame, text="历史数据上传", padding=10)
        upload_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(upload_frame, text="上传单个文件",
                  command=self.upload_single_file,
                  style="Action.TButton").pack(anchor=tk.W, pady=2)
        
        ttk.Button(upload_frame, text="批量上传文件夹",
                  command=self.upload_directory,
                  style="Action.TButton").pack(anchor=tk.W, pady=2)
        
        ttk.Button(upload_frame, text="上传ZIP文件",
                  command=self.upload_zip_file,
                  style="Action.TButton").pack(anchor=tk.W, pady=2)
    
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
    
    def create_analysis_tab(self):
        """创建投研分析标签页"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="投研分析")
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(analysis_frame, text="分析控制", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 品种选择
        ttk.Label(control_frame, text="选择分析品种:").pack(anchor=tk.W)
        self.analysis_exchange_var = tk.StringVar()
        analysis_exchange_combo = ttk.Combobox(control_frame, 
                                             textvariable=self.analysis_exchange_var,
                                             width=15)
        analysis_exchange_combo.pack(pady=(0, 5))
        analysis_exchange_combo.bind('<<ComboboxSelected>>', self.on_analysis_exchange_selected)
        
        self.analysis_product_var = tk.StringVar()
        self.analysis_product_combo = ttk.Combobox(control_frame,
                                                 textvariable=self.analysis_product_var,
                                                 width=15)
        self.analysis_product_combo.pack(pady=(0, 10))
        
        # 分析类型选择
        ttk.Label(control_frame, text="分析类型:").pack(anchor=tk.W)
        analysis_types = ["综合技术分析", "维科夫量价分析", "趋势强度分析", "震荡识别", "支撑阻力分析"]
        self.analysis_type_var = tk.StringVar()
        analysis_type_combo = ttk.Combobox(control_frame,
                                         textvariable=self.analysis_type_var,
                                         values=analysis_types,
                                         width=15)
        analysis_type_combo.pack(pady=(0, 10))
        analysis_type_combo.set("综合技术分析")
        
        # 执行分析按钮
        ttk.Button(control_frame, text="执行分析",
                  command=self.execute_analysis,
                  style="Action.TButton").pack(pady=5)
        
        ttk.Button(control_frame, text="生成交易信号",
                  command=self.generate_trading_signals,
                  style="Action.TButton").pack(pady=5)
        
        # 右侧结果显示区域
        result_frame = ttk.LabelFrame(analysis_frame, text="分析结果", padding=10)
        result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.analysis_result_text = scrolledtext.ScrolledText(result_frame, height=25)
        self.analysis_result_text.pack(fill=tk.BOTH, expand=True)
    
    def create_backtest_tab(self):
        """创建回测标签页"""
        backtest_frame = ttk.Frame(self.notebook)
        self.notebook.add(backtest_frame, text="策略回测")
        
        # 左侧参数设置
        param_frame = ttk.LabelFrame(backtest_frame, text="回测参数", padding=10)
        param_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 品种选择
        ttk.Label(param_frame, text="回测品种:").pack(anchor=tk.W)
        self.backtest_exchange_var = tk.StringVar()
        backtest_exchange_combo = ttk.Combobox(param_frame,
                                             textvariable=self.backtest_exchange_var,
                                             width=15)
        backtest_exchange_combo.pack(pady=(0, 5))
        backtest_exchange_combo.bind('<<ComboboxSelected>>', self.on_backtest_exchange_selected)
        
        self.backtest_product_var = tk.StringVar()
        self.backtest_product_combo = ttk.Combobox(param_frame,
                                                 textvariable=self.backtest_product_var,
                                                 width=15)
        self.backtest_product_combo.pack(pady=(0, 10))
        
        # 回测参数
        ttk.Label(param_frame, text="初始资金:").pack(anchor=tk.W)
        self.initial_capital_var = tk.StringVar(value="100000")
        ttk.Entry(param_frame, textvariable=self.initial_capital_var, width=15).pack(pady=(0, 5))
        
        ttk.Label(param_frame, text="手续费率:").pack(anchor=tk.W)
        self.commission_var = tk.StringVar(value="0.0003")
        ttk.Entry(param_frame, textvariable=self.commission_var, width=15).pack(pady=(0, 5))
        
        ttk.Label(param_frame, text="仓位比例:").pack(anchor=tk.W)
        self.position_size_var = tk.StringVar(value="0.1")
        ttk.Entry(param_frame, textvariable=self.position_size_var, width=15).pack(pady=(0, 10))
        
        # 日期范围
        ttk.Label(param_frame, text="回测开始日期:").pack(anchor=tk.W)
        self.backtest_start_date = DateEntry(param_frame, width=12,
                                           background='darkblue',
                                           foreground='white',
                                           borderwidth=2,
                                           date_pattern='y-mm-dd')
        self.backtest_start_date.pack(pady=(0, 5))
        self.backtest_start_date.set_date(datetime.now() - timedelta(days=365))
        
        ttk.Label(param_frame, text="回测结束日期:").pack(anchor=tk.W)
        self.backtest_end_date = DateEntry(param_frame, width=12,
                                         background='darkblue',
                                         foreground='white',
                                         borderwidth=2,
                                         date_pattern='y-mm-dd')
        self.backtest_end_date.pack(pady=(0, 10))
        
        # 开始回测按钮
        ttk.Button(param_frame, text="开始回测",
                  command=self.start_backtest,
                  style="Action.TButton").pack(pady=10)
        
        # 右侧结果显示
        result_frame = ttk.LabelFrame(backtest_frame, text="回测结果", padding=10)
        result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.backtest_result_text = scrolledtext.ScrolledText(result_frame, height=25)
        self.backtest_result_text.pack(fill=tk.BOTH, expand=True)
    
    def create_live_trading_tab(self):
        """创建实盘交易标签页"""
        trading_frame = ttk.Frame(self.notebook)
        self.notebook.add(trading_frame, text="实盘交易")
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(trading_frame, text="交易控制", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 交易接口选择
        ttk.Label(control_frame, text="交易接口:").pack(anchor=tk.W)
        interface_types = ["模拟交易", "CTA接口"]
        self.trading_interface_var = tk.StringVar()
        interface_combo = ttk.Combobox(control_frame,
                                     textvariable=self.trading_interface_var,
                                     values=interface_types,
                                     width=15)
        interface_combo.pack(pady=(0, 10))
        interface_combo.set("模拟交易")
        
        # 连接控制
        ttk.Button(control_frame, text="连接交易系统",
                  command=self.connect_trading_system,
                  style="Action.TButton").pack(pady=2)
        
        ttk.Button(control_frame, text="断开连接",
                  command=self.disconnect_trading_system,
                  style="Small.TButton").pack(pady=2)
        
        # 交易控制
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="启动自动交易",
                  command=self.start_auto_trading,
                  style="Action.TButton").pack(pady=2)
        
        ttk.Button(control_frame, text="停止自动交易",
                  command=self.stop_auto_trading,
                  style="Small.TButton").pack(pady=2)
        
        # 状态显示
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        self.trading_status_label = ttk.Label(control_frame, text="状态: 未连接",
                                            style="Status.TLabel")
        self.trading_status_label.pack(anchor=tk.W)
        
        # 右侧状态显示
        status_frame = ttk.LabelFrame(trading_frame, text="交易状态", padding=10)
        status_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.trading_status_text = scrolledtext.ScrolledText(status_frame, height=25)
        self.trading_status_text.pack(fill=tk.BOTH, expand=True)
        
        # 定时更新交易状态
        self.update_trading_status()
    
    # 新增的事件处理方法
    def on_analysis_exchange_selected(self, event=None):
        """分析页面交易所选择事件"""
        exchange = self.analysis_exchange_var.get()
        if exchange:
            products = db_manager.get_available_products(exchange)
            self.analysis_product_combo['values'] = products
            if products:
                self.analysis_product_var.set(products[0])
    
    def on_backtest_exchange_selected(self, event=None):
        """回测页面交易所选择事件"""
        exchange = self.backtest_exchange_var.get()
        if exchange:
            products = db_manager.get_available_products(exchange)
            self.backtest_product_combo['values'] = products
            if products:
                self.backtest_product_var.set(products[0])
    
    def execute_analysis(self):
        """执行技术分析"""
        def analysis_thread():
            try:
                self.start_progress()
                
                exchange = self.analysis_exchange_var.get()
                product = self.analysis_product_var.get()
                analysis_type = self.analysis_type_var.get()
                
                if not all([exchange, product]):
                    self.update_status("请选择交易所和品种")
                    return
                
                # 获取数据
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
                
                data = db_manager.get_continuous_contract_data(
                    exchange=exchange,
                    product_code=product,
                    contract_type='main',
                    start_date=start_date,
                    end_date=end_date
                )
                
                if data.empty:
                    self.update_status("没有找到符合条件的数据")
                    return
                
                # 执行分析
                if analysis_type == "综合技术分析":
                    result = self.comprehensive_technical_analysis(data, exchange, product)
                elif analysis_type == "维科夫量价分析":
                    result = self.wyckoff_analysis(data, exchange, product)
                elif analysis_type == "趋势强度分析":
                    result = self.trend_strength_analysis(data, exchange, product)
                elif analysis_type == "震荡识别":
                    result = self.sideways_analysis(data, exchange, product)
                elif analysis_type == "支撑阻力分析":
                    result = self.support_resistance_analysis(data, exchange, product)
                else:
                    result = "未知的分析类型"
                
                # 在主线程中更新结果
                self.root.after(0, lambda: self.display_analysis_result(result))
                
            except Exception as e:
                self.update_status(f"分析执行失败: {e}")
            finally:
                self.stop_progress()
        
        threading.Thread(target=analysis_thread, daemon=True).start()
    
    def comprehensive_technical_analysis(self, data: pd.DataFrame, exchange: str, product: str) -> str:
        """综合技术分析"""
        try:
            # 重命名列以匹配技术指标模块的期望
            analysis_data = data.rename(columns={
                'open_price': 'open',
                'high_price': 'high',
                'low_price': 'low',
                'close_price': 'close'
            })
            
            # 执行综合分析
            indicators = tech_indicators.comprehensive_analysis(analysis_data)
            
            # 生成交易建议
            recommendation = signal_generator.generate_trading_recommendation(analysis_data)
            
            # 格式化结果
            result = f"=== {exchange}-{product} 综合技术分析报告 ===\n\n"
            result += f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            result += f"数据范围: {data['trade_date'].min()} 至 {data['trade_date'].max()}\n"
            result += f"数据条数: {len(data)} 条\n\n"
            
            # 当前价格信息
            latest_data = data.iloc[-1]
            result += "=== 当前价格信息 ===\n"
            result += f"最新价格: {latest_data['close_price']:.2f}\n"
            result += f"开盘价: {latest_data['open_price']:.2f}\n"
            result += f"最高价: {latest_data['high_price']:.2f}\n"
            result += f"最低价: {latest_data['low_price']:.2f}\n"
            result += f"成交量: {latest_data['volume']:,.0f}\n\n"
            
            # 技术指标
            if indicators:
                result += "=== 主要技术指标 ===\n"
                latest_idx = -1
                
                if 'sma_20' in indicators and len(indicators['sma_20']) > 0:
                    sma20 = indicators['sma_20'].iloc[latest_idx]
                    result += f"SMA(20): {sma20:.2f}\n"
                
                if 'ema_12' in indicators and len(indicators['ema_12']) > 0:
                    ema12 = indicators['ema_12'].iloc[latest_idx]
                    result += f"EMA(12): {ema12:.2f}\n"
                
                if 'rsi' in indicators and len(indicators['rsi']) > 0:
                    rsi = indicators['rsi'].iloc[latest_idx]
                    result += f"RSI(14): {rsi:.2f}\n"
                
                if 'adx' in indicators and len(indicators['adx']) > 0:
                    adx = indicators['adx'].iloc[latest_idx]
                    result += f"ADX: {adx:.2f}\n"
                
                if 'trend_strength' in indicators and len(indicators['trend_strength']) > 0:
                    trend_str = indicators['trend_strength'].iloc[latest_idx]
                    result += f"趋势强度: {trend_str:.3f}\n\n"
            
            # 交易建议
            if recommendation:
                result += "=== 交易建议 ===\n"
                result += f"建议: {recommendation.get('recommendation', 'N/A')}\n"
                result += f"操作: {recommendation.get('action', 'N/A')}\n"
                result += f"信号强度: {recommendation.get('signal_strength', 0):.3f}\n"
                result += f"市场状态: {recommendation.get('market_regime', 'N/A')}\n\n"
                
                # 支撑阻力位
                support_levels = recommendation.get('support_levels', [])
                resistance_levels = recommendation.get('resistance_levels', [])
                
                if support_levels:
                    result += "支撑位: " + ", ".join([f"{level:.2f}" for level in support_levels]) + "\n"
                if resistance_levels:
                    result += "阻力位: " + ", ".join([f"{level:.2f}" for level in resistance_levels]) + "\n"
            
            return result
            
        except Exception as e:
            return f"综合技术分析失败: {e}"
    
    def wyckoff_analysis(self, data: pd.DataFrame, exchange: str, product: str) -> str:
        """维科夫量价分析"""
        try:
            result = f"=== {exchange}-{product} 维科夫量价分析 ===\n\n"
            
            # 计算维科夫指标
            ad_line = tech_indicators.wyckoff_accumulation_distribution(
                data['high_price'], data['low_price'], data['close_price'], data['volume']
            )
            pvt = tech_indicators.wyckoff_price_volume_trend(data['close_price'], data['volume'])
            
            # 成交量分析
            volume_profile = tech_indicators.volume_profile(
                data['high_price'], data['low_price'], data['close_price'], data['volume']
            )
            
            # 分析结果
            latest_ad = ad_line.iloc[-1] if len(ad_line) > 0 else 0
            latest_pvt = pvt.iloc[-1] if len(pvt) > 0 else 0
            
            result += f"累积/分布线(A/D): {latest_ad:.0f}\n"
            result += f"价量趋势(PVT): {latest_pvt:.0f}\n\n"
            
            # 成交量分布分析
            if volume_profile:
                poc_price = volume_profile.get('poc_price', 0)
                total_volume = volume_profile.get('total_volume', 0)
                result += f"成交量集中价位(POC): {poc_price:.2f}\n"
                result += f"总成交量: {total_volume:,.0f}\n\n"
            
            # 趋势判断
            ad_trend = "上升" if latest_ad > ad_line.iloc[-10] else "下降"
            pvt_trend = "上升" if latest_pvt > pvt.iloc[-10] else "下降"
            
            result += f"A/D线趋势: {ad_trend}\n"
            result += f"PVT趋势: {pvt_trend}\n\n"
            
            # 维科夫信号
            price_rising = data['close_price'].iloc[-1] > data['close_price'].iloc[-5]
            ad_falling = latest_ad < ad_line.iloc[-5]
            
            if price_rising and ad_falling:
                result += "⚠️ 警告: 价格上涨但A/D线下降，可能存在看跌背离\n"
            elif not price_rising and latest_ad > ad_line.iloc[-5]:
                result += "📈 机会: 价格下跌但A/D线上升，可能存在看涨背离\n"
            else:
                result += "📊 价格与A/D线趋势一致\n"
            
            return result
            
        except Exception as e:
            return f"维科夫分析失败: {e}"
    
    def trend_strength_analysis(self, data: pd.DataFrame, exchange: str, product: str) -> str:
        """趋势强度分析"""
        try:
            result = f"=== {exchange}-{product} 趋势强度分析 ===\n\n"
            
            trend_strength = tech_indicators.trend_strength(data['close_price'])
            adx_data = tech_indicators.adx(data['high_price'], data['low_price'], data['close_price'])
            
            latest_trend = trend_strength.iloc[-1] if len(trend_strength) > 0 else 0
            latest_adx = adx_data['adx'].iloc[-1] if 'adx' in adx_data and len(adx_data['adx']) > 0 else 0
            
            result += f"趋势强度指标: {latest_trend:.3f}\n"
            result += f"ADX指标: {latest_adx:.2f}\n\n"
            
            # 趋势评估
            if latest_trend > 0.7:
                trend_desc = "极强趋势"
            elif latest_trend > 0.5:
                trend_desc = "强趋势"
            elif latest_trend > 0.3:
                trend_desc = "中等趋势"
            else:
                trend_desc = "弱趋势或震荡"
            
            result += f"趋势评估: {trend_desc}\n"
            
            if latest_adx > 25:
                adx_desc = "趋势强劲"
            elif latest_adx > 20:
                adx_desc = "趋势中等"
            else:
                adx_desc = "趋势较弱"
            
            result += f"ADX评估: {adx_desc}\n\n"
            
            # 交易建议
            if latest_trend > 0.5 and latest_adx > 25:
                result += "💡 建议: 适合趋势跟随策略\n"
            elif latest_trend < 0.3 and latest_adx < 20:
                result += "💡 建议: 适合震荡交易策略\n"
            else:
                result += "💡 建议: 谨慎观望，等待明确趋势\n"
            
            return result
            
        except Exception as e:
            return f"趋势强度分析失败: {e}"
    
    def sideways_analysis(self, data: pd.DataFrame, exchange: str, product: str) -> str:
        """震荡识别分析"""
        try:
            result = f"=== {exchange}-{product} 震荡识别分析 ===\n\n"
            
            sideways = tech_indicators.sideways_market_detection(
                data['high_price'], data['low_price'], data['close_price']
            )
            
            breakout_data = tech_indicators.breakout_potential(
                data['high_price'], data['low_price'], data['close_price'], data['volume']
            )
            
            # 当前状态
            is_sideways = sideways.iloc[-1] if len(sideways) > 0 else 0
            
            if is_sideways:
                result += "📊 当前状态: 震荡市场\n\n"
                
                # 震荡区间
                recent_data = data.tail(20)
                support_level = recent_data['low_price'].min()
                resistance_level = recent_data['high_price'].max()
                
                result += f"震荡区间:\n"
                result += f"  支撑位: {support_level:.2f}\n"
                result += f"  阻力位: {resistance_level:.2f}\n"
                result += f"  区间幅度: {(resistance_level - support_level) / support_level * 100:.2f}%\n\n"
                
                # 突破潜力分析
                if 'bb_squeeze' in breakout_data:
                    bb_squeeze = breakout_data['bb_squeeze'].iloc[-1]
                    volume_spike = breakout_data['volume_spike'].iloc[-1]
                    
                    if bb_squeeze:
                        result += "⚠️ 布林带收缩，可能即将突破\n"
                    if volume_spike:
                        result += "📈 成交量异常放大\n"
                    
                    if bb_squeeze and volume_spike:
                        result += "💥 高突破概率！建议关注方向选择\n"
                
            else:
                result += "📈 当前状态: 趋势市场\n"
                
                # 趋势方向
                price_change = (data['close_price'].iloc[-1] - data['close_price'].iloc[-20]) / data['close_price'].iloc[-20]
                direction = "上涨" if price_change > 0 else "下跌"
                result += f"趋势方向: {direction}\n"
                result += f"20日涨跌幅: {price_change * 100:.2f}%\n"
            
            return result
            
        except Exception as e:
            return f"震荡识别分析失败: {e}"
    
    def support_resistance_analysis(self, data: pd.DataFrame, exchange: str, product: str) -> str:
        """支撑阻力分析"""
        try:
            result = f"=== {exchange}-{product} 支撑阻力分析 ===\n\n"
            
            sr_levels = tech_indicators.support_resistance_levels(
                data['high_price'], data['low_price'], data['close_price']
            )
            
            current_price = data['close_price'].iloc[-1]
            result += f"当前价格: {current_price:.2f}\n\n"
            
            # 支撑位分析
            support_levels = sr_levels.get('support_levels', [])
            if support_levels:
                result += "📉 主要支撑位:\n"
                for i, level in enumerate(support_levels[:5]):
                    distance = (current_price - level) / current_price * 100
                    result += f"  支撑{i+1}: {level:.2f} (距离: {distance:.2f}%)\n"
                result += "\n"
            
            # 阻力位分析
            resistance_levels = sr_levels.get('resistance_levels', [])
            if resistance_levels:
                result += "📈 主要阻力位:\n"
                for i, level in enumerate(resistance_levels[:5]):
                    distance = (level - current_price) / current_price * 100
                    result += f"  阻力{i+1}: {level:.2f} (距离: {distance:.2f}%)\n"
                result += "\n"
            
            # 关键位分析
            nearest_support = max([level for level in support_levels if level < current_price], default=0)
            nearest_resistance = min([level for level in resistance_levels if level > current_price], default=float('inf'))
            
            if nearest_support > 0:
                support_distance = (current_price - nearest_support) / current_price * 100
                result += f"🔻 最近支撑位: {nearest_support:.2f} (距离: {support_distance:.2f}%)\n"
            
            if nearest_resistance < float('inf'):
                resistance_distance = (nearest_resistance - current_price) / current_price * 100
                result += f"🔺 最近阻力位: {nearest_resistance:.2f} (距离: {resistance_distance:.2f}%)\n"
            
            # 交易建议
            result += "\n💡 交易建议:\n"
            if nearest_support > 0 and support_distance < 2:
                result += "- 接近支撑位，关注反弹机会\n"
            if nearest_resistance < float('inf') and resistance_distance < 2:
                result += "- 接近阻力位，注意回调风险\n"
            
            return result
            
        except Exception as e:
            return f"支撑阻力分析失败: {e}"
    
    def display_analysis_result(self, result: str):
        """显示分析结果"""
        self.analysis_result_text.delete(1.0, tk.END)
        self.analysis_result_text.insert(1.0, result)
    
    def generate_trading_signals(self):
        """生成交易信号"""
        def signal_thread():
            try:
                self.start_progress()
                
                exchange = self.analysis_exchange_var.get()
                product = self.analysis_product_var.get()
                
                if not all([exchange, product]):
                    self.update_status("请选择交易所和品种")
                    return
                
                # 获取数据
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                
                data = db_manager.get_continuous_contract_data(
                    exchange=exchange,
                    product_code=product,
                    contract_type='main',
                    start_date=start_date,
                    end_date=end_date
                )
                
                if data.empty:
                    self.update_status("没有找到符合条件的数据")
                    return
                
                # 重命名列
                signal_data = data.rename(columns={
                    'open_price': 'open',
                    'high_price': 'high',
                    'low_price': 'low',
                    'close_price': 'close'
                })
                
                # 生成信号
                signal_result = signal_generator.comprehensive_signal(signal_data)
                
                # 格式化结果
                result = f"=== {exchange}-{product} 交易信号分析 ===\n\n"
                result += f"信号生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                if signal_result:
                    final_signals = signal_result['final_signal']
                    signal_stats = signal_result['signal_stats']
                    
                    # 最新信号
                    latest_signal = final_signals.iloc[-1] if len(final_signals) > 0 else 0
                    latest_strength = signal_result['weighted_signal'].iloc[-1] if len(signal_result['weighted_signal']) > 0 else 0
                    
                    signal_desc = {
                        2: "强烈买入",
                        1: "买入",
                        0: "观望",
                        -1: "卖出",
                        -2: "强烈卖出"
                    }
                    
                    result += f"当前信号: {signal_desc.get(latest_signal, '未知')}\n"
                    result += f"信号强度: {latest_strength:.3f}\n\n"
                    
                    # 信号统计
                    result += "=== 信号统计 ===\n"
                    result += f"总信号数: {signal_stats['total_signals']}\n"
                    result += f"买入信号: {signal_stats['buy_signals']}\n"
                    result += f"卖出信号: {signal_stats['sell_signals']}\n"
                    result += f"强烈买入: {signal_stats['strong_buy']}\n"
                    result += f"强烈卖出: {signal_stats['strong_sell']}\n\n"
                    
                    # 各个子信号
                    individual_signals = signal_result['individual_signals']
                    result += "=== 各指标信号 ===\n"
                    
                    signal_names = {
                        'ma_crossover': '均线交叉',
                        'macd': 'MACD',
                        'rsi': 'RSI',
                        'bollinger': '布林带',
                        'wyckoff': '维科夫',
                        'support_resistance': '支撑阻力',
                        'trend_following': '趋势跟随',
                        'breakout': '突破'
                    }
                    
                    for signal_key, signal_series in individual_signals.items():
                        if len(signal_series) > 0:
                            latest_individual = signal_series.iloc[-1]
                            signal_name = signal_names.get(signal_key, signal_key)
                            result += f"{signal_name}: {signal_desc.get(latest_individual, '观望')}\n"
                
                # 在主线程中更新结果
                self.root.after(0, lambda: self.display_analysis_result(result))
                
            except Exception as e:
                self.update_status(f"信号生成失败: {e}")
            finally:
                self.stop_progress()
        
        threading.Thread(target=signal_thread, daemon=True).start()
    
    def start_backtest(self):
        """开始回测"""
        def backtest_thread():
            try:
                self.start_progress()
                
                exchange = self.backtest_exchange_var.get()
                product = self.backtest_product_var.get()
                
                if not all([exchange, product]):
                    self.update_status("请选择回测品种")
                    return
                
                # 获取回测参数
                initial_capital = float(self.initial_capital_var.get())
                commission = float(self.commission_var.get())
                position_size = float(self.position_size_var.get())
                start_date = self.backtest_start_date.get()
                end_date = self.backtest_end_date.get()
                
                # 获取数据
                data = db_manager.get_continuous_contract_data(
                    exchange=exchange,
                    product_code=product,
                    contract_type='main',
                    start_date=start_date,
                    end_date=end_date
                )
                
                if data.empty:
                    self.update_status("没有找到回测数据")
                    return
                
                # 重命名列
                backtest_data = data.rename(columns={
                    'open_price': 'open',
                    'high_price': 'high',
                    'low_price': 'low',
                    'close_price': 'close'
                })
                
                # 创建回测引擎
                from backtest_engine import BacktestEngine
                engine = BacktestEngine(
                    initial_capital=initial_capital,
                    commission=commission,
                    position_size_pct=position_size
                )
                
                # 运行回测
                symbol = f"{exchange}-{product}"
                report = engine.run_backtest(backtest_data, symbol)
                
                # 格式化结果
                result = self.format_backtest_result(report, exchange, product)
                
                # 在主线程中更新结果
                self.root.after(0, lambda: self.display_backtest_result(result))
                
            except Exception as e:
                self.update_status(f"回测执行失败: {e}")
            finally:
                self.stop_progress()
        
        threading.Thread(target=backtest_thread, daemon=True).start()
    
    def format_backtest_result(self, report: dict, exchange: str, product: str) -> str:
        """格式化回测结果"""
        if not report:
            return "回测失败，无结果数据"
        
        summary = report.get('summary', {})
        
        result = f"=== {exchange}-{product} 回测报告 ===\n\n"
        result += f"回测完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        result += "=== 资金表现 ===\n"
        result += f"初始资金: {summary.get('initial_capital', 0):,.2f}\n"
        result += f"最终资金: {summary.get('final_capital', 0):,.2f}\n"
        result += f"总收益率: {summary.get('total_return', 0):.2%}\n"
        result += f"年化收益率: {summary.get('annual_return', 0):.2%}\n"
        result += f"波动率: {summary.get('volatility', 0):.2%}\n"
        result += f"夏普比率: {summary.get('sharpe_ratio', 0):.3f}\n"
        result += f"最大回撤: {summary.get('max_drawdown', 0):.2%}\n\n"
        
        result += "=== 交易统计 ===\n"
        result += f"总交易次数: {summary.get('total_trades', 0)}\n"
        result += f"盈利次数: {summary.get('winning_trades', 0)}\n"
        result += f"亏损次数: {summary.get('losing_trades', 0)}\n"
        result += f"胜率: {summary.get('win_rate', 0):.2%}\n"
        result += f"盈亏比: {summary.get('profit_factor', 0):.3f}\n"
        result += f"平均盈利: {summary.get('avg_win', 0):.2f}\n"
        result += f"平均亏损: {summary.get('avg_loss', 0):.2f}\n\n"
        
        # 策略评估
        total_return = summary.get('total_return', 0)
        sharpe_ratio = summary.get('sharpe_ratio', 0)
        max_drawdown = summary.get('max_drawdown', 0)
        win_rate = summary.get('win_rate', 0)
        
        result += "=== 策略评估 ===\n"
        
        if total_return > 0.1:
            result += "✅ 收益表现: 优秀\n"
        elif total_return > 0.05:
            result += "🔶 收益表现: 良好\n"
        else:
            result += "❌ 收益表现: 不佳\n"
        
        if sharpe_ratio > 1.5:
            result += "✅ 风险调整收益: 优秀\n"
        elif sharpe_ratio > 1.0:
            result += "🔶 风险调整收益: 良好\n"
        else:
            result += "❌ 风险调整收益: 不佳\n"
        
        if max_drawdown < 0.1:
            result += "✅ 回撤控制: 优秀\n"
        elif max_drawdown < 0.2:
            result += "🔶 回撤控制: 良好\n"
        else:
            result += "❌ 回撤控制: 不佳\n"
        
        if win_rate > 0.5:
            result += "✅ 胜率: 优秀\n"
        elif win_rate > 0.4:
            result += "🔶 胜率: 良好\n"
        else:
            result += "❌ 胜率: 不佳\n"
        
        return result
    
    def display_backtest_result(self, result: str):
        """显示回测结果"""
        self.backtest_result_text.delete(1.0, tk.END)
        self.backtest_result_text.insert(1.0, result)
    
    def connect_trading_system(self):
        """连接交易系统"""
        interface_type = self.trading_interface_var.get()
        
        if interface_type == "模拟交易":
            success = live_trading_manager.initialize_interface("simulated")
            if success:
                success = live_trading_manager.connect_to_trading_system({})
        else:
            success = live_trading_manager.initialize_interface("cta")
            if success:
                success = live_trading_manager.connect_to_trading_system({})
        
        if success:
            self.trading_status_label.config(text="状态: 已连接")
            self.update_status("交易系统连接成功")
        else:
            self.trading_status_label.config(text="状态: 连接失败")
            self.update_status("交易系统连接失败")
    
    def disconnect_trading_system(self):
        """断开交易系统连接"""
        # 这里应该调用断开连接的方法
        self.trading_status_label.config(text="状态: 未连接")
        self.update_status("已断开交易系统连接")
    
    def start_auto_trading(self):
        """启动自动交易"""
        success = live_trading_manager.start_live_trading()
        if success:
            self.update_status("自动交易已启动")
        else:
            self.update_status("启动自动交易失败")
    
    def stop_auto_trading(self):
        """停止自动交易"""
        live_trading_manager.stop_live_trading()
        self.update_status("自动交易已停止")
    
    def update_trading_status(self):
        """更新交易状态"""
        try:
            status = live_trading_manager.get_trading_status()
            
            status_text = "=== 交易系统状态 ===\n\n"
            status_text += f"连接状态: {'已连接' if status.get('connected', False) else '未连接'}\n"
            status_text += f"自动交易: {'运行中' if status.get('bot_running', False) else '已停止'}\n\n"
            
            account_info = status.get('account_info')
            if account_info:
                status_text += "=== 账户信息 ===\n"
                status_text += f"账户余额: {account_info.balance:,.2f}\n"
                status_text += f"可用资金: {account_info.available_cash:,.2f}\n"
                status_text += f"总市值: {account_info.total_value:,.2f}\n\n"
            
            positions = status.get('positions', [])
            if positions:
                status_text += "=== 持仓信息 ===\n"
                for pos in positions:
                    status_text += f"{pos.symbol}: {pos.quantity} 手, 均价: {pos.avg_price:.2f}\n"
            else:
                status_text += "=== 持仓信息 ===\n无持仓\n"
            
            # 更新显示
            self.trading_status_text.delete(1.0, tk.END)
            self.trading_status_text.insert(1.0, status_text)
            
        except Exception as e:
            self.logger.error(f"更新交易状态失败: {e}")
        
        # 每5秒更新一次
        self.root.after(5000, self.update_trading_status)
    
    def upload_single_file(self):
        """上传单个文件"""
        file_path = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            # 简化的上传对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("文件上传配置")
            dialog.geometry("400x200")
            
            ttk.Label(dialog, text="合约代码:").pack(pady=5)
            symbol_var = tk.StringVar()
            ttk.Entry(dialog, textvariable=symbol_var, width=30).pack(pady=5)
            
            ttk.Label(dialog, text="交易所:").pack(pady=5)
            exchange_var = tk.StringVar()
            exchange_combo = ttk.Combobox(dialog, textvariable=exchange_var, 
                                        values=list(EXCHANGES.keys()), width=27)
            exchange_combo.pack(pady=5)
            
            def do_upload():
                symbol = symbol_var.get()
                exchange = exchange_var.get()
                
                if not symbol or not exchange:
                    messagebox.showerror("错误", "请填写完整信息")
                    return
                
                def upload_thread():
                    try:
                        self.start_progress()
                        result = data_uploader.upload_file(file_path, symbol, exchange)
                        
                        if result['success']:
                            self.update_status(f"文件上传成功: {result['message']}")
                            self.root.after(0, self.update_data_summary)
                        else:
                            self.update_status(f"文件上传失败: {result['message']}")
                        
                        dialog.destroy()
                        
                    except Exception as e:
                        self.update_status(f"文件上传失败: {e}")
                    finally:
                        self.stop_progress()
                
                threading.Thread(target=upload_thread, daemon=True).start()
            
            ttk.Button(dialog, text="开始上传", command=do_upload).pack(pady=20)
    
    def upload_directory(self):
        """批量上传文件夹"""
        directory = filedialog.askdirectory(title="选择数据文件夹")
        
        if directory:
            # 交易所选择对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("批量上传配置")
            dialog.geometry("300x150")
            
            ttk.Label(dialog, text="默认交易所:").pack(pady=10)
            exchange_var = tk.StringVar()
            exchange_combo = ttk.Combobox(dialog, textvariable=exchange_var,
                                        values=list(EXCHANGES.keys()), width=20)
            exchange_combo.pack(pady=5)
            
            def do_batch_upload():
                exchange = exchange_var.get()
                
                def upload_thread():
                    try:
                        self.start_progress()
                        result = data_uploader.batch_upload_directory(directory, exchange)
                        
                        summary = result.get('summary', {})
                        message = summary.get('message', '批量上传完成')
                        
                        self.update_status(f"批量上传完成: {message}")
                        self.root.after(0, self.update_data_summary)
                        
                        dialog.destroy()
                        
                    except Exception as e:
                        self.update_status(f"批量上传失败: {e}")
                    finally:
                        self.stop_progress()
                
                threading.Thread(target=upload_thread, daemon=True).start()
            
            ttk.Button(dialog, text="开始上传", command=do_batch_upload).pack(pady=20)
    
    def upload_zip_file(self):
        """上传ZIP文件"""
        file_path = filedialog.askopenfilename(
            title="选择ZIP文件",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        
        if file_path:
            def upload_thread():
                try:
                    self.start_progress()
                    result = data_uploader.extract_and_upload_zip(file_path)
                    
                    summary = result.get('summary', {})
                    message = summary.get('message', 'ZIP文件上传完成')
                    
                    self.update_status(f"ZIP上传完成: {message}")
                    self.root.after(0, self.update_data_summary)
                    
                except Exception as e:
                    self.update_status(f"ZIP上传失败: {e}")
                finally:
                    self.stop_progress()
            
            threading.Thread(target=upload_thread, daemon=True).start()
    
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
