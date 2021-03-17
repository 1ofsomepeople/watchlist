from flask import Flask, render_template
from flask import url_for, redirect, flash, request
import os
import sys
import click
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
app = Flask(__name__)

#数据库配置
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:////'+os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False #关闭对类型的监控
app.config['SECRET_KEY']='dev'#设置签名所需的密钥
#在扩展类实例化之前加载配置
db=SQLAlchemy(app)

login_manager = LoginManager(app)#实例化扩展类
login_manager.login_view = 'login'
@login_manager.user_loader
def load_user(user_id):#创建用户加载回调函数，接收用户id
  user = User.query.get(int(user_id))#查询用户
  return user

#创建数据库类型
class User(db.Model, UserMixin):
  id=db.Column(db.Integer, primary_key=True)#主键
  name=db.Column(db.String(20))#名字
  username=db.Column(db.String(20))#用户名
  password_hash=db.Column(db.String(128))#密码

  def set_password(self, password):#设置密码
    self.password_hash=generate_password_hash(password)
  
  def validate_password(self, password):#验证密码
    return check_password_hash(self.password_hash, password)

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

@app.route('/', methods=['GET', 'POST'])#主页视图函数，可以处理GET和POST请求
def index():
  if request.method == 'POST':
    if not current_user.is_authenticated:#如果当前用户未认证
      return redirect(url_for('index'))#重定向到主页
    #获取表单数据
    title = request.form.get('title')
    year = request.form.get('year')
    #判断数据格式
    if not title or not year or len(year)>4 or len(title)>60:
      flash('Invalid input.')#显示错误提示
      return redirect(url_for('index'))#重定向到主页
    #保存表单数据到数据库
    movie = Movie(title=title, year=year)
    db.session.add(movie)#添加到数据库会话
    db.session.commit()#提交到数据库
    flash('Item create.')
    return redirect(url_for('index'))
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

@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):#编辑电影条目
  movie = Movie.query.get_or_404(movie_id)

  if request.method == 'POST':
    title = request.form['title']
    year = request.form['year']
    if not title or not year or len(year)>4 or len(title)>60:
      flash('Invalid input.')#显示错误提示
      return redirect(url_for('edit', movie_id=movie_id))#重定向到主页
    movie.title = title
    movie.year = year
    db.session.commit()
    flash('Item updated')
    return redirect(url_for('index'))
  return render_template('edit.html', movie=movie)

@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete(movie_id):
  movie = Movie.query.get_or_404(movie_id)
  db.session.delete(movie)
  db.session.commit()
  flash('Item deleted.')
  return redirect(url_for('index'))

#创建管理员账户
@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
  """Create user."""
  db.create_all()
  user = User.query.first()
  if user is not None:
    click.echo('Updating user...')
    user.username = username
    user.set_password(password)
  else:
    click.echo('Creating user...')
    user = User(username=username, name='Admin')
    user.set_password(password)
    db.session.add(user)
  db.session.commit()
  click.echo('Done.')

#用户登录视图函数
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    if not username or not password:
      flash('Invalid input.')
      return redirect(url_for('login'))
    user = User.query.first()
    #验证用户名与密码
    if username == user.username and user.validate_password(password):
      login_user(user)#登入
      flash('Login success.')
      return redirect(url_for('index'))
    flash('Invalid username or password.')
    return redirect(url_for('login'))
  return render_template('login.html')

#用户登出视图函数
@app.route('/logout')
@login_required #视图保护
def logout():
  logout_user()
  flash('Logout.')
  return redirect(url_for('index'))

#支持设置用户名
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
  if request.method == 'POST':
    name = request.form['name']
    if not name or len(name)>20:
      flash('Invalid input.')
      return redirect(url_for('setting'))
    
    current_user.name = name
    # current_user会返回当前登录用户的数据库记录对象
    # 等同于下面的用法
    # user = User.query.first()
    # user.name = name
    db.session.commit()
    flash('Setting updated.')
    return redirect(url_for('index'))
  return render_template('settings.html')