from flask import Flask, render_template
from flask import url_for
import os
import sys
import click
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

#数据库配置
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:////'+os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False #关闭对类型的监控
#在扩展类实例化之前加载配置
db=SQLAlchemy(app)

#创建数据库类型
class User(db.Model):
  id=db.Column(db.Integer, primary_key=True)#主键
  name=db.Column(db.String(20))#名字

class Movie(db.Model):
  id=db.Column(db.Integer, primary_key=True)
  title=db.Column(db.String(60))
  year=db.Column(db.String(4))

#自定义命令
@app.cli.command()#命令注册
@click.option('--drop', is_flag=True, help='Create after drop.')#设置选项
def initdb(drop):
  """ Initialize the database. """
  if drop:
    db.drop_all()
  db.create_all()
  click.echo('Initialize the database.')#输出提示信息

@app.route('/')#主页视图函数
def index():
  # user = User.query.first()#读取用户记录 由于使用了模板上下文函数，user变量可直接使用
  movies = Movie.query.all()#读取所有电影记录
  return render_template('index.html',movies=movies)

@app.route('/user/<name>')
def user_page(name):
  return'<h1>hello: %s!<h1/>' % name

@app.route('/test')
def test_url_for():
  print(url_for('hello'))
  print(url_for('user_page', name='peter'))
  print(url_for('test_url_for'))
  print(url_for('test_url_for', num=2))
  return 'Test page'

@app.cli.command()
def forge():
  """Generate fake data."""
  db.create_all()
  name = 'Grey Li'
  movies = [
    {'title':'My Neighbor Totoro', 'year': '1988'},
    {'title':'Dead Poets Society', 'year': '1989'},
    {'title':'A Perfect World', 'year': '1993'},
    {'title':'Leon', 'year': '1994'},
    {'title':'Mahjong', 'year': '1996'},
    {'title':'Swallowtail Butterfly', 'year': '1996'},
    {'title':'King of Comedy', 'year': '1999'},
    {'title':'Devils on the Doorstep', 'year': '1999'},
    {'title':'WALL-E', 'year': '2008'},
    {'title':'The Pork of Music', 'year': '2012'}
  ]
  user = User(name=name)
  db.session.add(user)
  for m in movies:
    movie = Movie(title=m['title'], year=m['year'])
    db.session.add(movie)
  db.session.commit()
  click.echo('Done.')

@app.errorhandler(404) #错误处理函数，传入要处理的错误代码
def page_not_found(e):#接收异常对象作为参数
  # user = User.query.first() #使用模板上下文函数，user变量可直接使用
  return render_template('404.html'), 404 #返回状态和状态码

'''模板上下文处理函数，这个函数返回的变量（以字典键值对的形式）
将会统一注入到每一个模板的上下文环境中，因此可以直接在模板中使用。
同样的，后面创建的任何一个模板，都可以在其中直接使用user变量。'''
@app.context_processor
def inject_user():#函数名自定义
  user=User.query.first()
  return dict(user=user)#需要返回字典，等同于 return {'user':user}
