#from kivy.app import App
from kivymd.app import MDApp
#from kivymd.uix.pickers import MDDockedDatePicker
from kivymd.uix.pickers import MDModalDatePicker
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserIconView
#from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle, Line
from kivy.utils import get_color_from_hex
import re
import sqlite3
from kivy.uix.image import Image
#from kivy.reload import Reloader
from PIL import Image as PILImage,ImageFont,ImageWin
from PIL import ImageDraw
from io import BytesIO
#from datepicker import DatePicker
#from datepicker import CalendarWidget
import numpy as np
import pandas as pd
import qrcode
import os
#import datetime
from kivy.uix.camera import Camera  
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
import mysql.connector
from escpos.printer import Usb
# from escpos import BluetoothConnection
from kivy.uix.spinner import Spinner
# import pymysql
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from mysql.connector import Error
import mysql.connector
from pyzbar.pyzbar import decode
import bcrypt
from kivy.metrics import dp
import win32print
import win32ui
import requests 
from reportlab.lib.pagesizes import mm  # Add this import statement
from reportlab.pdfgen import canvas


conn = mysql.connector.connect(
    host="192.168.20.17",
    user="itadmin",
    password="itadmin@2018",
    database="asset_management"
)

if conn.is_connected():
    print("Connected to database")
    
    cursor=conn.cursor()
    
    cursor.execute("SELECT*FROM asset")
    rows=cursor.fetchall()
    
    for row in rows:
        print(row)
        
    cursor.close()
    conn.close()
    
else:
    print("Connection failed")

    
class LoginPage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Login Page'

        # Set font for labels, text inputs, and button
        label_font = {'font_name': 'RobotoMono-Regular.ttf', 'font_size': dp(20)}
        input_font = {'font_name': 'RobotoMono-Regular.ttf', 'font_size': dp(20), 'size_hint_y': None, 'height': dp(50)}
        button_font = {'font_name': 'RobotoMono-Regular.ttf', 'font_size': dp(20), 'size_hint_y': None, 'height': dp(50)}

        self.username_input = TextInput(hint_text='Username', multiline=False, **input_font)
        self.password_input = TextInput(hint_text='Password', multiline=False, password=True, **input_font)
        self.login_button = Button(text='Login', **button_font)
        self.login_button.bind(on_press=self.login)

        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(40))
        layout.add_widget(Label(text='GWI Asset Management System', size_hint=(1, 0.2), **label_font))
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        layout.add_widget(self.login_button)

        self.add_widget(layout)
        
    def login(self, instance):
        username = self.username_input.text
        password = self.password_input.text
        if self.validate_login(username, password):
            self.manager.current = 'asset_management'
        else:
            self.show_error_popup('Invalid username or password')

    def validate_login(self, username, password):
        try:
            mydb = mysql.connector.connect(
                host="192.168.20.17",
                user="itadmin",
                password="itadmin@2018",
                database="asset_management"
            )
            mycursor = mydb.cursor()
            sql = "SELECT * FROM user WHERE username = %s AND password = %s"
            val = (username, password)
            mycursor.execute(sql, val)
            user = mycursor.fetchone()
            mycursor.close()
            if user:
                return True
            else:
                return False
        except mysql.connector.Error as err:
            print("Something went wrong: {}".format(err))
            return False

    def show_error_popup(self, message):
        content = BoxLayout(orientation='vertical', padding=dp(10))
        content.add_widget(Label(text=message, size_hint=(1, None), height=dp(50)))
        popup = Popup(title='Error', content=content, size_hint=(None, None), size=(dp(300), dp(150)))
        popup.open()


class AssetManagement(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.username_label = Label(text='', font_size=20, font_name='RobotoMono-Regular.ttf')  # Placeholder for username label
        # Other initialization code
        self.title = 'Asset Management Page'
        self.layout = None  # Initialize layout as None
        self.username = None  # Initialize username attribute
        self.validation_results = {}  # Initialize an empty dictionary to store validation results
        self.assets = []
        self.db_conn = None  # Placeholder for database connection
        self.db_cursor = None
        self.engine = None
        self.inv_no_input = TextInput()  # Define the inv_no_input attribute
        self.logout_button = Button(text='Logout', size_hint=(None, None), size=(80, 40), font_name='RobotoMono-Regular.ttf')  # Logout button
        self.logout_button.bind(on_press=self.logout)  # Bind logout button to logout method

        # Connect to the MySQL database
        self.connect_to_database()

        # Load assets from the database
        self.load_assets()
        
        # Navbar buttons
        self.import_button = Button(text='Import', size_hint=(None, None), size=(150, 50))
        self.import_button.bind(on_release=self.show_filechooser)
        self.add_new_button = Button(text='Create Asset', size_hint=(None, None), size=(150, 50))
        self.add_new_button.bind(on_release=self.show_add_new_popup)
        self.camera_button = Button(text='Scan QR', size_hint=(None, None), size=(100, 50))
        self.camera_button.bind(on_release=self.show_camera_popup)

    def connect_to_database(self):
        try:
            self.db_conn = mysql.connector.connect(
                host="192.168.20.17",
                user="itadmin",
                password="itadmin@2018",
                database="asset_management"
            )
            self.db_cursor = self.db_conn.cursor()
            db_url = URL.create(
                drivername="mysql+mysqlconnector",
                username="itadmin",
                password="itadmin@2018",
                host="192.168.20.17",
                database="asset_management"
            )
            self.engine = create_engine(db_url)
            print("Successfully connected to the database")
        except Error as err:
            print("Error connecting to MySQL database:", err)

    def load_assets(self):
        if self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                query = "SELECT * FROM asset_management.asset"
                cursor.execute(query)
                self.assets = cursor.fetchall()
                cursor.close()
            except mysql.connector.Error as err:
                print("Error fetching assets from database:", err)

    def on_enter(self, *args):
        super().on_enter(*args)
        if not self.layout:
            self.layout = self.create_layout()
            self.add_widget(self.layout)
        if self.logout_button.parent:
            self.logout_button.parent.remove_widget(self.logout_button)
        # Add logout button to the top bar
        top_bar = self.layout.children[-1]
        top_bar.add_widget(self.logout_button)
    
        # Add navbar
        self.create_navbar()
    
        # Set username label text if username is not None  
        if self.username is not None:
            self.username_label.text = self.username
            self.username_label.pos = (20, Window.height - 50)
            self.add_widget(self.username_label)
    
    def create_navbar(self):
        navbar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=50)
        
        # Adjust the size_hint_x to be equally distributed
        self.import_button.size_hint_x = 1
        self.add_new_button.size_hint_x = 1
        self.camera_button.size_hint_x = 1
        
        navbar.add_widget(self.import_button)
        navbar.add_widget(self.add_new_button)
        navbar.add_widget(self.camera_button)
        
        self.layout.add_widget(navbar, index=0)
        
    def set_username(self, username):
        self.username = username
        
    def logout(self, instance):
        self.manager.current = 'login'  # Switch to login screen
    
    # Import process
    def show_filechooser(self, instance):
        content = BoxLayout(orientation='vertical')
        filechooser = FileChooserIconView(filters=['*.xlsx'])
        content.add_widget(filechooser)

        btn_select = Button(text='Select', size_hint=(1, 0.2))
        btn_select.bind(on_release=lambda x: self.load_excel(filechooser.selection))
        content.add_widget(btn_select)

        self.popup = Popup(title='Select Excel File', content=content, size_hint=(0.9, 0.9))
        self.popup.open()
        
    def load_excel(self, selection):
        if selection:
            try:
                file_path = selection[0]
                
                # Define the columns you want to import
                columns_to_import = [
                    'id', 'asset_desc', 'division', 'tag_no', 'pur_date', 
                    'qty', 'inv_no', 'supplier', 'cost', 'location'
                ]
                self.df = pd.read_excel(file_path, usecols=columns_to_import)
                
                #self.df = pd.read_excel(file_path)
                self.popup.dismiss()
                self.show_data_popup()
            except Exception as e:
                self.popup.dismiss()
                self.show_error_popup(str(e))
    
    def show_data_popup(self):
        content = BoxLayout(orientation='vertical')
        scrollview = ScrollView(size_hint=(1, 0.8))
        grid = GridLayout(cols=len(self.df.columns), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        # Add headers
        for column in self.df.columns:
            grid.add_widget(Label(text=str(column), bold=True, size_hint_y=None, height=40))

        # Add data rows
        for index, row in self.df.iterrows():
            for cell in row:
                grid.add_widget(TextInput(text=str(cell), readonly=True, size_hint_y=None, height=30))

        scrollview.add_widget(grid)
        content.add_widget(scrollview)

        btn_save = Button(text='Save Data', size_hint=(1, 0.2))
        btn_save.bind(on_release=self.save_data)  # Bind the save method to the button
        content.add_widget(btn_save)

        self.popup = Popup(title='Imported Data', content=content, size_hint=(0.9, 0.9))
        self.popup.open()
        
    
    def save_data(self, instance):
        try:
            # Check if the data already exists in the database
            with self.db_conn.cursor(dictionary=True) as cursor:
                for _, row in self.df.iterrows():
                    query = "SELECT COUNT(*) as count FROM asset WHERE id = %s"
                    cursor.execute(query, (row['id'],))
                    result = cursor.fetchone()
                    if result['count'] > 0:
                        self.show_error_popup(f"Error: Asset with ID {row['id']} already exists in the database.")
                        return
            
            # Insert the data into the MySQL database
            self.df.to_sql('asset', self.engine, if_exists='append', index=False)
            self.show_success_popup("Data saved successfully")
        except Exception as e:
            self.show_error_popup(f"Error saving data: {str(e)}")

    
    # Error import
    def show_error_popup(self, message):
        content = BoxLayout(orientation='vertical')
        label = Label(text=message)
        btn_close = Button(text='Close', size_hint=(1, 0.2))
        btn_close.bind(on_release=lambda x: self.popup.dismiss())
        content.add_widget(label)
        content.add_widget(btn_close)

        self.popup = Popup(title='Error', content=content, size_hint=(0.6, 0.6))
        self.popup.open()
    
    # Success import
    def show_success_popup(self, message):
        content = BoxLayout(orientation='vertical')
        label = Label(text=message)
        btn_close = Button(text='Close', size_hint=(1, 0.2))
        btn_close.bind(on_release=lambda x: self.popup.dismiss())
        content.add_widget(label)
        content.add_widget(btn_close)

        self.popup = Popup(title='Success', content=content, size_hint=(0.6, 0.6))
        self.popup.open()
    # Finish Import process
    
    
    def show_add_new_popup(self, instance):
        content = BoxLayout(orientation='vertical')
        self.inputs = []
        
        # Ensure cursor is initialized
        if not self.db_cursor:
            self.show_error_popup("Database cursor not initialized")
            return

        # Query to get the next auto-increment ID
        try:
            self.db_cursor.execute("SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'asset_management' AND TABLE_NAME = 'asset'")
            next_id = self.db_cursor.fetchone()[0]
        except mysql.connector.Error as err:
            self.show_error_popup(f"Error: {err}")
            return

        # Query to get the next auto-increment ID
        self.db_cursor.execute("SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'asset'")
        next_id = self.db_cursor.fetchone()[0]

        # Fields to be added
        fields = ['ID', 'Description', 'Division', 'Tag No', 'Purchase Date', 'Quantity', 'Invoice No', 'Supplier', 'Cost', 'Location']

        # Create input fields for each field
        for field in fields:
            box = BoxLayout(orientation='horizontal')
            label = Label(text=str(field), size_hint=(0.3, 1))
            
            if field == 'ID':
                # Create a read-only TextInput for ID
                text_input = TextInput(text=str(next_id), size_hint=(0.7, 1), readonly=True)
                
            elif field == 'Purchase Date':
                # Create a DatePicker for the Purchase Date
                text_input = TextInput(readonly=True, size_hint=(0.7, 1))
                text_input.bind(focus=self.show_date_picker)
                
            else:
                text_input = TextInput(size_hint=(0.7, 1))
                
            box.add_widget(label)
            box.add_widget(text_input)
            content.add_widget(box)
            self.inputs.append(text_input)

        btn_add = Button(text='Add', size_hint=(1, 0.2))
        btn_add.bind(on_release=self.add_new_data)
        content.add_widget(btn_add)

        self.popup = Popup(title='Add New Data', content=content, size_hint=(0.9, 0.9))
        self.popup.open()
        
    #Date picker configurations
    def show_date_picker(self, instance, value):
        if value:
            self.date_picker_target = instance
            date_picker = MDModalDatePicker()
            date_picker.bind(on_ok=self.on_ok, on_cancel=self.on_cancel)
            date_picker.open()

    def on_ok(self, instance_date_picker):
        
        selected_date = instance_date_picker.get_date()[0]
        
        # Format the date as "YYYY-MM-DD"
        formatted_date = selected_date.strftime("%Y-%m-%d")
        
        # Set the selected date to the TextInput that opened the date picker
        self.date_picker_target.text = str(formatted_date)
        print(f"Selected date: {selected_date}")
        instance_date_picker.dismiss()
                
    def on_cancel(self, instance):
        # Close the date picker without doing anything
        instance.dismiss()
        print("Calendar Dismissed")
                

    def add_new_data(self, instance):
        new_data = [input.text for input in self.inputs]
        if None in new_data or '' in new_data:
            self.show_error_popup("Please fill in all fields")
            return

        try:
            # Insert query without 'ID' as it is auto-incremented
            query = """INSERT INTO asset (asset_desc, division, tag_no, pur_date, qty, inv_no, supplier, cost, location) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            self.db_cursor.execute(query, tuple(new_data[1:]))  # Exclude the ID field for insertion
            self.db_conn.commit()
            self.popup.dismiss()
            self.show_info_popup("New asset added successfully!")
            self.load_assets()  # Reload assets from the database to update the screen
        except mysql.connector.Error as err:
            self.show_error_popup(f"Error: {err}")
    
    def show_error_popup(self, message):
        popup = Popup(title='Error', content=Label(text=message), size_hint=(0.9, 0.9))
        popup.open()

    def show_info_popup(self, message):
        popup = Popup(title='Info', content=Label(text=message), size_hint=(0.9, 0.9))
        popup.open()

            
    def show_camera_popup(self, instance):
        self.camera = Camera(play=True, resolution=(640, 480), size_hint=(1, 0.8))
        btn_close = Button(text='Close', size_hint=(1, 0.2))
        btn_close.bind(on_release=self.close_camera_popup)

        content = BoxLayout(orientation='vertical')
        content.add_widget(self.camera)
        content.add_widget(btn_close)

        self.popup = Popup(title='Scan QR Code', content=content, size_hint=(0.9, 0.9))
        self.popup.open()

        # Start the QR code scanning process
        Clock.schedule_interval(self.detect_qr_code, 1.0 / 30.0)

    def close_camera_popup(self, instance):
        self.camera.play = False
        self.popup.dismiss()
        Clock.unschedule(self.detect_qr_code)

    def detect_qr_code(self, dt):
        if self.camera.texture:
            # Convert Kivy texture to OpenCV image
            texture = self.camera.texture
            size = texture.size
            pixels = texture.pixels

            # Convert the Kivy texture to a numpy array
            frame = np.frombuffer(pixels, np.uint8).reshape(size[1], size[0], 4)

            if frame is not None:
                # Convert from RGBA to RGB
                frame = frame[:, :, :3]

                # Convert to PIL Image
                pil_image = Image.fromarray(frame)

                # Decode QR codes
                decoded_objects = decode(pil_image)

                for obj in decoded_objects:
                    qr_code_data = obj.data.decode("utf-8")
                    print("QR Code detected: ", qr_code_data)
                    self.close_camera_popup(None)
                    self.show_info_popup(f"QR Code detected: {qr_code_data}")
                    return

    def show_info_popup(self, message):
        content = BoxLayout(orientation='vertical')
        label = Label(text=message)
        btn_close = Button(text='Close')
        btn_close.bind(on_release=lambda x: self.popup.dismiss())

        content.add_widget(label)
        content.add_widget(btn_close)

        self.popup = Popup(title='Information', content=content, size_hint=(0.5, 0.5))
        self.popup.open()

    def show_error_popup(self, message):
        self.show_info_popup(f"Error: {message}")

    def create_layout(self):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=40)

        # Top bar for title and logout button
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        title_label = Label(text='Asset Management', font_name='RobotoMono-Regular.ttf', font_size=30, color=(0, 0, 0, 1), bold=True, valign='middle')
        top_bar.add_widget(title_label)
        top_bar.add_widget(self.logout_button)  # Add logout button to the top bar
        
        layout.add_widget(top_bar)
        
        # Change background color
        with layout.canvas.before:
            Color(rgb=get_color_from_hex('#f0f0f0'))
            self.rect = Rectangle(size=layout.size, pos=layout.pos)

        # Bind size and pos to update background color when resized
        layout.bind(size=self._update_background, pos=self._update_background)

        # Input fields
        input_layout = GridLayout(cols=2, spacing=5, size_hint=(1, None), height=120)

        # ID Input
        input_layout.add_widget(Label(text='ID:', font_name='RobotoMono-Regular.ttf', font_size=20,
                                    color=(0, 0, 0, 1)))
        self.id_input = TextInput(hint_text='Enter ID', font_name='RobotoMono-Regular.ttf',
                                font_size=18, foreground_color=(0, 0, 0, 1))
        input_layout.add_widget(self.id_input)

        # Tag No Input
        input_layout.add_widget(Label(text='Tag No:', font_name='RobotoMono-Regular.ttf', font_size=20,
                                    color=(0, 0, 0, 1)))
        self.tag_no_input = TextInput(hint_text='Enter Tag No', font_name='RobotoMono-Regular.ttf',
                                    font_size=18, foreground_color=(0, 0, 0, 1))
        input_layout.add_widget(self.tag_no_input)

        # Invoice No Input
        input_layout.add_widget(Label(text='Invoice No:', font_name='RobotoMono-Regular.ttf', font_size=20,
                                    color=(0, 0, 0, 1)))
        self.invoice_no_input = TextInput(hint_text='Enter Invoice No', font_name='RobotoMono-Regular.ttf',
                                        font_size=18, foreground_color=(0, 0, 0, 1))
        input_layout.add_widget(self.invoice_no_input)

        layout.add_widget(input_layout)
        

        # Search button
        search_button = Button(text='Search', size_hint=(1, None), height=40, font_name='RobotoMono-Regular.ttf',
                                font_size=18, color=(1, 1, 1, 1))
        search_button.bind(on_press=self.search_assets)
        layout.add_widget(search_button)

        # Result table
        result_label = Label(text='Search Results:', font_name='RobotoMono-Regular.ttf', font_size=20,bold=True,
                            size_hint=(1, None), height=20, color=(0, 0, 0, 1))
        layout.add_widget(result_label)

        # Create the result grid
        self.result_grid = GridLayout(cols=4, spacing=10, padding=(10, 10), size_hint_y=None)
        self.result_grid.bind(minimum_height=self.result_grid.setter('height'))

        # Create the ScrollView
        scroll_view = ScrollView(size_hint=(1, None), size=(Window.width, Window.height - 400))
        scroll_view.add_widget(self.result_grid)

        layout.add_widget(scroll_view)

        return layout

    def _update_background(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        
    def search_assets(self, instance):
        # Clear previous search results
        self.result_grid.clear_widgets()    

        # Get search criteria from input fields
        search_id = self.id_input.text.strip()
        search_tag_no = self.tag_no_input.text.strip()
        search_invoice_no = self.invoice_no_input.text.strip()

        # Perform search in the database
        if self.db_conn:
            try:
                with self.db_conn.cursor(dictionary=True) as cursor:
                    query = "SELECT * FROM asset_management.asset WHERE 1=1"
                    params = []

                    if search_id:
                        query += " AND id = %s"
                        params.append(search_id)
                    if search_tag_no:
                        query += " AND tag_no = %s"
                        params.append(search_tag_no)
                    if search_invoice_no:
                        query += " AND inv_no = %s"
                        params.append(search_invoice_no)

                    cursor.execute(query, params)
                    matching_assets = cursor.fetchall()

                    # Display search results in the result grid
                    if matching_assets:
                        for asset in matching_assets:
                            self.add_asset_to_grid(asset)
                    else:
                        self.display_no_results_message()

            except mysql.connector.Error as err:
                print("Error searching assets in database:", err)
                # Display error message to user interface

    
    
    def add_asset_to_grid(self, asset):
        id = asset['id']
        asset_desc=asset['asset_desc']
        division=asset['division']
        tag_no = asset['tag_no']
        pur_date=asset['pur_date']
        qty=asset['qty']
        inv_no = asset['inv_no']
        supplier=asset['supplier']
        cost=asset['cost']
        location=asset['location']
        
        # Check if the header row is already present
        if len(self.result_grid.children) < 5:  # Assuming 5 widgets in header row
            # Add headers to the result grid
            headers = ['ID', 'Tag No', 'Invoice No', 'Print QR']
            for header in headers:
                header_label = Label(text=header, font_size=30, bold=True, italic=True, color=(0,0 , 1, 1),
                            size_hint_y=None, height=40, halign='center', valign='middle')
                header_label.bind(size=header_label.setter('text_size'))
                self.result_grid.add_widget(header_label)


        # Add asset info to grid
        for key in ['id', 'tag_no', 'inv_no']:
            label = Label(
                text=str(asset[key]),
                font_size=25,
                color=(0, 0, 0, 1),
                size_hint_y=None,
                height=30,
                halign='center',
                valign='middle'
            )
            self.result_grid.add_widget(label)
        
        # Generate QR code
        qr_button_container = BoxLayout(orientation='horizontal', size_hint=(None, None), size=(100, 30), padding=(0, 0, 0, 1))
        generate_qr_button = Button(text='Generate QR', size_hint=(None, None), size=(300, 30), halign='center', valign='middle',
                                     background_color=(0.1, 0.7, 0.5, 1), color=(1, 1, 1, 1))
        generate_qr_button.bind(on_press=lambda instance: self.generate_qr_code(id,asset_desc,division, tag_no,pur_date,qty, inv_no,supplier,cost,location))
        qr_button_container.add_widget(generate_qr_button)
        generate_qr_button.pos_hint = {'center_x': 0.5}
        self.result_grid.add_widget(qr_button_container)



    def display_no_results_message(self):
        no_results_label = Label(
            text="No matching assets found.",
            font_name='RobotoMono-Regular.ttf',
            font_size=16,
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=30,
            halign='center',
            valign='middle'
        )
        self.result_grid.add_widget(no_results_label)
        
        
    def generate_qr_code(self, id,asset_desc,division, tag_no,pur_date,qty, inv_no,supplier,cost,location):
            # Combine asset information
            asset_info = f"Asset ID: {id}\n\nAsset desc: {asset_desc}\n\nDivision: {division}\n\nTag No: {tag_no}\n\nPurchase Date: {pur_date}\n\nQuantity: {qty}\n\nInvoice No: {inv_no}\n\nSupplier: {supplier}\n\nCost: {cost}\n\nLocation: {location}"

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(asset_info)
            qr.make(fit=True)

            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_image_path = f"{id}_qr.png"
            qr_image.save(qr_image_path)

            # Resize the image to fit on the screen
            qr_image = qr_image.resize((40, 30))

            # Display QR code image on QRCodeScreen
            self.display_qr_code_on_screen(id, tag_no, inv_no, qr_image_path)

    def display_qr_code_on_screen(self, id, tag_no, inv_no, qr_image_path):
            # Switch to QRCodeScreen
            self.manager.current = 'qr_code'

            # Get the QRCodeScreen instance
            qr_code_screen = self.manager.get_screen('qr_code')

            # Initialize the QRCodeScreen with the parameters
            qr_code_screen.__init__(id=id, tag_no=tag_no, inv_no=inv_no, qr_image=qr_image_path)


class QRCodeScreen(Screen):
    def __init__(self, id=None, tag_no=None, inv_no=None, qr_image=None, **kwargs):
        super().__init__(**kwargs)
        self.asset_id = id
        self.tag_no = tag_no
        self.inv_no = inv_no
        self.qr_image = qr_image
        self.create_layout()

    def create_layout(self):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)

        # Title container
        title_container = BoxLayout(orientation='vertical', size_hint_y=None, height=120)
        title_label = Label(text='Generated QR Code', font_name='RobotoMono-Regular.ttf', font_size=32, color=(0, 0, 0, 1),
                            valign='top', size_hint_y=None, height=80)
        title_container.add_widget(title_label)

        # Change background color
        with layout.canvas.before:
            Color(rgb=get_color_from_hex('#f0f0f0'))
            self.rect = Rectangle(size=layout.size, pos=layout.pos)

        # Bind size and pos to update background color when resized
        layout.bind(size=self._update_background, pos=self._update_background)

        layout.add_widget(title_container)

        # Centered QR Code image
        qr_code_container = BoxLayout(orientation='vertical', size_hint_y=None, height=300)
        qr_code_container.add_widget(Label())  # Spacer
        qr_code_image = Image(source=self.qr_image, size_hint=(None, None), size=(300, 300))
        qr_code_container.add_widget(qr_code_image)
        qr_code_container.add_widget(Label())  # Spacer
        layout.add_widget(qr_code_container)

        # Center the qr_code_image horizontally within its parent qr_code_container
        qr_code_image.pos_hint = {'center_x': 0.5}

        # Tag No and Invoice No display
        tag_label = Label(text=f"Tag No: {self.tag_no}", font_name='RobotoMono-Regular.ttf', font_size=20, color=(0, 0, 0, 1))
        layout.add_widget(tag_label)

        inv_label = Label(text=f"Invoice No: {self.inv_no}", font_name='RobotoMono-Regular.ttf', font_size=20, color=(0, 0, 0, 1))
        layout.add_widget(inv_label)

        # Print button
        print_button = Button(text='Print', size_hint=(1, None), height=50, font_name='RobotoMono-Regular.ttf',
                                font_size=18, color=(1, 1, 1, 1))
        print_button.bind(on_press=self.print_qr)
        layout.add_widget(print_button)

        # Back button
        back_button = Button(text='Back', size_hint=(1, None), height=50, font_name='RobotoMono-Regular.ttf',
                                font_size=18, color=(1, 1, 1, 1))
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def _update_background(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def print_qr(self, instance):
        """
        Print the QR code with the associated serial number.

        Parameters:
            instance: The button instance that triggered the print action.
        """
        # Define the desired size in millimeters
        desired_width_mm = 40
        desired_height_mm = 30

        # Convert millimeters to points (1 inch = 25.4 mm)
        mm = 25.4 / 1.0
        desired_width_pts = mm * desired_width_mm
        desired_height_pts = mm * desired_height_mm

        # Create a PIL image object
        image = Image.new('RGB', (int(desired_width_pts), int(desired_height_pts)), color='white')
        draw = ImageDraw.Draw(image)

        # Load the QR code image
        qr_code = Image.open(self.qr_image)
        qr_code = qr_code.resize((280, 280))
        image.paste(qr_code, (10, 10))

        # Add serial number text
        draw.text((10, 300), f"Tag No: {self.tag_no}", fill='black')
        draw.text((10, 320), f"Invoice No: {self.inv_no}", fill='black')

        # Create a PDF document
        c = canvas.Canvas("printed_qr_code.pdf", pagesize=(desired_width_pts, desired_height_pts))
        c.drawImage(image, 0, 0, width=desired_width_pts, height=desired_height_pts)
        c.showPage()
        c.save()

        print("Image printed successfully.")


    def go_back(self, instance):
            self.manager.current = 'asset_management'


class MainApp(MDApp):
    def build(self):
        sm = ScreenManager()

        # Check if the 'login' screen is already added to the ScreenManager
        if 'login' not in sm.screen_names:
            login_page = LoginPage(name='login')
            sm.add_widget(login_page)

        # Check if the 'asset_management' screen is already added to the ScreenManager
        if 'asset_management' not in sm.screen_names:
            asset_management_page = AssetManagement(name='asset_management')
            sm.add_widget(asset_management_page)
            
        # Check if the 'qr_code' screen is already added to the ScreenManager
        if 'qr_code' not in sm.screen_names:
            qr_code_screen = QRCodeScreen(name='qr_code')
            sm.add_widget(qr_code_screen)

        return sm

if __name__ == '__main__':
    MainApp().run()