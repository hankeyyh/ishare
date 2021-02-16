# ishare
instagram-like social website based on flask
![explore](https://github.com/hankeyyh/ishare/blob/master/img2.png)
# installation
clone:
```
$ git clone https://github.com/hankeyyh/ishare.git
$ cd ishare
```
install:
```
$ pip install -r requirements
```
create `.env` and add:
```
MAIL_SERVER = smtp.your_mail_server.com
MAIL_USERNAME = your_mail_username
MAIL_PASSWORD = your_mail_password
```
generate fake data then run:
```
$ flask forge
$ flask run
```
