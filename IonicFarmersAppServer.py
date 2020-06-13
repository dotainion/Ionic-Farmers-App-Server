import flask
from flask import Flask,request,send_file,Response,jsonify
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import sqlite3
import smtplib
import re
from json import dumps
from flask_cors import CORS
import uuid
import base64
import os



app = Flask(__name__)
CORS(app)
cors = CORS(app, resources={r"/*":{"origins":"*"}})

class Database:
    class UserData:
        def __init__(self):
            """this database will store user personal info like username
            password address and contact information"""
            self.connection = sqlite3.connect('FarmerAppUserData.db')
            self.cursor = self.connection.cursor()
            self.cursor.execute("CREATE TABLE IF NOT EXISTS userdata (email TEXT, password TEXT,firstname TEXT,lastname TEXT,"
                                "homeaddress TEXT,shippingaddress TEXT,phonenumber TEXT,time TEXT,city TEXT)")
            self.tools = Tools()
            self.time = self.tools.Time()
        def insert(self,email,password,firstname,lastname,homeaddress,shippingaddress,phonenumber,city):
            if not self.isExist(email):
                self.cursor.execute("INSERT INTO userdata (email,password,firstname,lastname,homeaddress,shippingaddress,"
                                    "phonenumber,time,city) VALUES (?,?,?,?,?,?,?,?,?)",(email,password,firstname,lastname,homeaddress,
                                    shippingaddress,phonenumber,self.time.date(),city))
                self.connection.commit()
                return True
            return False
        def isExist(self, email):
            """This function is responsible for check to see of email already
            in the database and return tue it is else false if its not"""
            self.cursor.execute("SELECT email FROM userdata WHERE email = ?", (email,))
            username = self.cursor.fetchall()
            if username:
                for data in username[0]:
                    if data == email:
                        return True
            return False
        def checkCreds(self,username,password):
            self.cursor.execute("SELECT password FROM userdata WHERE email = ?",(username,))
            credentials = self.cursor.fetchall()[0]
            if credentials:
                for creds in credentials:
                    if creds == password:
                        return True
                return False
            return None
        def getCustomer(self,email):
            self.cursor.execute("SELECT firstname, lastname, phonenumber,homeaddress,shippingaddress FROM userdata WHERE email = ?", (email,))
            customer = self.cursor.fetchall()
            if customer:
                return customer[0]
            return None
    class Products:
        def __init__(self):
            """this database will stare products user uploaded for sale
            user email will be stored with item as user reference"""
            self.noRecordImgPath = r"C:\Users\user\Desktop\python GUI projects\errorimg.png"
            self.key = ["img", "id", "title", "price", "detail","email"]
            self.getThisAmount = 100
            self.tools = Tools()
            self.connection = sqlite3.connect('FarmerAppProducts.db')
            self.cursor = self.connection.cursor()
            self.cursor.execute("CREATE TABLE IF NOT EXISTS products (email TEXT,image TEXT, id TEXT,title TEXT,price TEXT,"
                                "detail TEXT,category TEXT,pickupaddress TEXT,time TEXT,status TEXT)")
            self.time = self.tools.Time()
        def dictionaryBuilder(self,arrayData):
            arrayBuilder = []
            for items in arrayData:
                img, id, title, price, detail, email = items
                arrayBuilder.append({self.key[0]: img, self.key[1]: self.tools.randId(), self.key[2]: title,
                                     self.key[3]: "$"+price, self.key[4]: detail, self.key[5]:email})
            return arrayBuilder
        def insert(self,email,image, _id,title,price,detail,category,pickupaddress):
            """this will insert user product into database with price and details
            image should be converted to base64 from the App before sending to database"""
            self.cursor.execute("INSERT INTO products (email,image, id,title,price,detail,category,pickupaddress,time,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                (email,image, _id,title,price,detail,category,pickupaddress,self.time.date(),"PENDING"))
            self.connection.commit()
        def get(self,getmore,search="",category=""):
            """this will get product data from database and return its data
            getmore will be passed in as the amount of data already displayed in the app
            so a for loop will run without doing anything until the amount is equal to
            or more than getmore then the rest of data will be append to an array then stop
            by a given value so a certain amount of data will be display in App at a time"""
            if category == "All Category" or category == "":
                if search == "":#search only by category only thats all
                    self.cursor.execute("SELECT image, id,title,price,detail,email FROM products")
                else:#search by category and reference input
                    self.cursor.execute("SELECT image, id,title,price,detail,email FROM products WHERE title LIKE ?",("%"+search+"%",))
            else:#this will search data
                if search == "":#search by spesific category only
                    self.cursor.execute("SELECT image, id,title,price,detail,email FROM products WHERE category LIKE ?",("%"+category+"%",))
                else:
                    self.cursor.execute("SELECT image, id,title,price,detail,email FROM products WHERE title LIKE ? AND category LIKE ?",("%"+search+"%","%"+category+"%"))
            products = self.cursor.fetchall()
            moredata = []
            if products:
                valueAmountcounter = 0
                for i, items in enumerate(products):
                    if i >= getmore:
                        valueAmountcounter += 1
                        moredata.append(items)
                        if valueAmountcounter >= self.getThisAmount:
                            break
                return Response(dumps(self.dictionaryBuilder(moredata)))
            else:
                noRecords = [{"img": self.tools.base64Convert(self.noRecordImgPath), "id": "1", "title": "No Records",
                              "price": "", "detail": "Please try a different search or change category"}]
                return Response(dumps(noRecords))
    class Transaction:
        def __init__(self):
            """this class is responsible for storing all purchase products"""
            self.key = ["id", "title", "price", "customer","time","qty","firstname","lastname"]
            self.connection = sqlite3.connect('FarmerAppTransactions.db')
            self.cursor = self.connection.cursor()
            self.cursor.execute(
                "CREATE TABLE IF NOT EXISTS purchase (customer TEXT,seller TEXT,title TEXT,price TEXT,quantity TEXT,status,time TEXT)")
            self.tools = Tools()
            self.time = self.tools.Time()
        def purchase(self,customer,seller,title,price,quantity):
            """this will store the information when a sale is made by a customer"""
            self.cursor.execute("INSERT INTO purchase (customer,seller,title,price,quantity,time,status) VALUES (?,?,?,?,?,?,?)",
                (customer,seller,title,price,quantity,self.time.date(),"PENDING"))
            self.connection.commit()
        def customerData(self,email):
            """this will return all sale that was made by a particular customer referencing his or her email address
            it place all item from a specific customer and place it in a array and return it inorder to seperat each
            customer information """
            self.cursor.execute("SELECT title,price,quantity,time FROM purchase WHERE status = 'PENDING' AND customer = ?",(email,))
            data = self.cursor.fetchall()
            if data:
                products = []
                for item in data:
                    products.append([item[0],item[2],item[1],item[3]])
                return products
            return None
        def deliveries(self,email):
            """this function will user farmer email as parameter to get all customer emails available for him or her of
            items that was sold the customer email will be stored in a array which also get all data available for that
            customer with the farmers email also as reeference and store it as a dictionary making the customer data
            store only once and his or her product information then return it"""
            self.cursor.execute("SELECT customer FROM purchase WHERE status = 'PENDING' AND seller = ?",(email,))
            data = self.cursor.fetchall()
            if data:
                DB = Database().UserData()
                holdCustomers = []
                nameHolder = []
                for customer in data:
                    if customer[0] not in nameHolder:
                        nameHolder.append(customer[0])
                        holdCustomers.append({"names":DB.getCustomer(customer[0]),"email":customer[0],"records":self.customerData(customer[0])})
                return holdCustomers
            return None

class Tools:
    class Time:
        def __init__(self):
            """this class is responsible for generating time"""
        def month(self):
            return datetime.datetime.now().month
        def day(self):
            return datetime.datetime.now().day
        def year(self):
            return datetime.datetime.now().year
        def time(self):
            times = datetime.datetime.now().time()
            tempstrip = ''
            for time in str(times):
                if time == ".":
                    break
                else:
                    tempstrip = tempstrip + time
            return tempstrip
        def date(self):
            return str(self.month()) + "/" + str(self.day()) + "/" + str(self.year())
    class Email:
        def __init__(self):
            pass
        def send(self, sendTo, contents):
            """NOTE...this will allow less secure app to communicate ... https://myaccount.google.com/lesssecureapps?pli=1
            if its not activated then emails will not be sent"""
            try:
                subject = "Password Restore"
                server = smtplib.SMTP('smtp.gmail.com', 587)  # or prot 465 or 587
                admin = 'areset0000@gmail.com'
                passw = 'meloneyblair1'
                msg = MIMEMultipart()
                msg['From'] = admin
                msg['To'] = sendTo
                msg['Subject'] = subject
                body = contents
                msg.attach(MIMEText(body, 'plain'))
                text = msg.as_string()
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(admin, passw)
                server.sendmail(admin, sendTo, text)
                server.close()
                return True
            except:
                return False
        def validate(self, email):
            """this will check to see if email is in correct format"""
            is_valid = re.search(r'[\w.-]+@[\w.-]+.\w+', email)
            if is_valid:
                return True
            return False
    def reversTupleInList(self,value):
        storeReversItem = []
        valueLength = len(value)
        for i in range(valueLength):
            storeReversItem.append(value[valueLength - i - 1])
        return storeReversItem
    def base64Convert(self,image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    def randId(self):
        RandomId = hash(str(uuid.uuid1())) % 10000000000
        return RandomId

@app.route('/sign/up', methods=['POST',"GET"])
def register():
    if request.method == "POST":
        credentials = request.get_json()
        if credentials["serverUserName"] == "user" and credentials["serverPassword"] == "users":
            DB = Database().UserData()
            firstName = credentials["firstname"]
            lastName = credentials["lastname"]
            email = credentials["username"]
            phoneNumber = credentials["phonenumber"]
            city = credentials["city"]
            homeAddress = credentials["homeaddress"]
            shippingAddress = credentials["shippingaddress"]
            password = credentials["password"]
            results = DB.insert(email,password,firstName,lastName,homeAddress,shippingAddress,phoneNumber,city)
            return str(results).lower()
        return "false"
    return jsonify("error")

@app.route('/recover_password')
def forgetPassword():
    return ""

@app.route('/login', methods=['POST',"GET"])
def login():
    if request.method == "POST":
        credentials = request.get_json()
        if credentials["serverusername"] == "user" and credentials["serverpassword"] == "users":
            DB = Database().UserData()
            username = credentials["username"]
            password = credentials["password"]
            results = str(DB.checkCreds(username,password)).lower()
            return results.lower()
    return jsonify("error")

@app.route('/buy/payments',methods=["POST"])
def processPaymentAndProducts():
    """this function will proccess payments and manage customer
    products they paid for so it can be delivered"""
    if request.method == "POST":
        paidFor = request.get_json()
        security = paidFor[0]
        if security["serverusername"] == "user" and security["serverpassword"] == "users":
            DB = Database().Transaction()
            for items in paidFor[1:]:
                name = items["productName"]
                farmer_email = items["sellerEmail"]
                price = items["price"]
                quantity = items["qty"]
                buyer_email = items["buyerEmail"]
                print(buyer_email,farmer_email,name,price,quantity)
                DB.purchase(buyer_email,farmer_email,name,price,quantity)
    return "hg"

@app.route('/notification')
def paymentInfo():
    return ""

@app.route('/transportations',methods=["GET","POST"])
def transportationsDeleveries():
    """this function will get specific farmers data that was sold and return it for delivery"""
    if request.method == "POST":
        credentials = request.get_json()
        if credentials["serverusername"] == "user" and credentials["serverpassword"] == "users":
            DB = Database().Transaction()
            farmerEmail = credentials["farmeremail"]
            resulsts = DB.deliveries(farmerEmail)
            print(resulsts)
            if resulsts:
                return jsonify(resulsts)
            return str(resulsts).lower()
        return "false"
    return "false"

@app.route('/farmers/product/upload',methods=["GET","POST"])
def formersProductUpload():
    """this function will get farmers data and upload it into database for sale"""
    if request.method == "POST":
        jsonData = request.get_json()
        if jsonData["serverusername"] == "user" and jsonData["serverpassword"] == "users":
            DB = Database().Products()
            email = jsonData["email"]
            image = jsonData["image"]
            other = jsonData["other"]
            category_value = jsonData["catValue"]
            product = jsonData["productValue"]
            delivery_address = jsonData["address"]
            price = jsonData["costValue"]
            description = jsonData["descritpion"]
            if not product:
                product = other
            DB.insert(email,image,"id",product,price,description,category_value,delivery_address)
            return "true"
        return "false"
    return "none"

@app.route('/see/products',methods=["GET","POST"])
def Products():
    """this will collect a sertain amount of data and return it into the app
    if the user request more then a certain amount will be send again
    the amount is amount 40 which is determine withing the database class
    the database call will return the data array as Response(dumps(data)) """
    DB = Database().Products()
    json_search = request.get_json()
    if json_search["serverusername"] == "user" and json_search["serverpassword"] == "users":
        try:
            if json_search["state"] == "true":
                search_reference = json_search["search"]
                search_cagegory = json_search["cagegory"]
                search_moreData = int(json_search["moreData"])#more data is to pull a certain amount of data again
                if search_cagegory == "All Category":
                    if search_moreData <= DB.getThisAmount:
                        if search_reference.strip(" ") == "":
                            return DB.get(getmore=search_moreData,search=search_cagegory)
                        else:
                            return DB.get(getmore=search_moreData,search=search_reference, category=search_cagegory)
                    else:
                        return DB.get(search_moreData, search_reference, search_cagegory)
                else:
                    if search_moreData <= DB.getThisAmount:
                        return DB.get(getmore=search_moreData,search=search_reference, category=search_cagegory)
                    else:
                        if search_reference.strip(" ") == "":
                            return DB.get(search_moreData, search_reference, search_cagegory)
                        else:
                            return DB.get(search_moreData, search_reference, search_cagegory)
                    #imgArrayBuilder.append({"img": tool.base64Convert(path + img), "id": tool.randId(), "title": "sometext", "price": "$" + str(i),"detail": "details"})
            return "false"
        except Exception as error:
            return DB.get(0)
    return 'false'


if __name__=="__main__":
    app.run(debug=True,host="127.0.0.1",port=os.environ.get("PORT",80))




