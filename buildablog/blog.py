import os
import re
from string import letters

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)

class MainPage(BlogHandler):
  def get(self):
      self.write('MYBLOG')

##### blog stuff

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

class BlogFront(BlogHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        t = jinja_env.get_template("front.html")
        response = t.render(posts=posts)
        self.response.out.write(response)

        #self.render('front.html', posts = posts)

class PostPage(BlogHandler):
    def get(self, id):
        #post = Post.get_by_id(int(id))

        key = db.Key.from_path('Post', int(id), parent=blog_key())
        post = db.get(key)

        if post:
            #self.render("permalink.html", post = post)
            t = jinja_env.get_template("permalink.html")
            response = t.render(post=post)
        else:
            #error = "there is no post with id %s" % id
            error = "The resource could not be found."
            t = jinja_env.get_template("404.html")
            response = t.render(error=error)
             #self.response.error.(404)

        self.response.out.write(response)


class NewPost(BlogHandler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/blog', BlogFront),
                               webapp2.Route('/blog/<id:\d+>', PostPage),
                               ('/blog/newpost', NewPost),
                               ],
                              debug=True)
