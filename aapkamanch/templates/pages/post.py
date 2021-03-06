# Copyright Aap Ka Manch
# License GNU General Public Licence

from __future__ import unicode_literals
import webnotes
from webnotes.utils import get_fullname
from aapkamanch.helpers import get_access

no_cache = 1

def get_context():
	post_name = webnotes.request.path[1:].split("/")[1]
	post = webnotes.bean("Post", post_name).doc
	
	access = get_access(post.unit)
	if not access.get("read"):
		return {
			"name": "Not Permitted",
			"title": "Not Permitted",
			"post_list_html": "<div class='text-muted'>You are not permitted to view this page</div>",
			"not_permitted": True
		}
	
	fullname = get_fullname(post.owner)
	title = "{post} by {fullname}".format(unit=post.unit, post="Post", fullname=fullname)
	unit = webnotes.bean("Unit", post.unit).doc
	parents = webnotes.conn.sql("""select name, unit_title from tabUnit 
		where lft <= %s and rgt >= %s order by lft asc""", (unit.lft, unit.rgt), as_dict=1)
	
	return {
		"name": post.unit,
		"title": title,
		"parent_post_html": get_parent_post_html(post, access),
		"post_list_html": get_child_posts_html(post),
		"parents": parents,
		"parent_post": post.name
	}
	
def get_parent_post_html(post, access):
	profile = webnotes.bean("Profile", post.owner).doc
	for fieldname in ("first_name", "last_name", "user_image", "fb_hometown", "fb_location"):
		post.fields[fieldname] = profile.fields[fieldname]
	
	return webnotes.get_template("templates/includes/inline_post.html")\
		.render({"post": post.fields, "write": access.get("write")})

def get_child_posts_html(post):
	if isinstance(post, basestring):
		post = webnotes.bean("Post", post).doc
	
	access = get_access(post.unit)
	if webnotes.local.form_dict.cmd=="get_child_posts_html":
		# for paging
		if not access.get("read"):
			raise webnotes.PermissionError
	
	posts = webnotes.conn.sql("""select p.name, p.unit, p.status, p.is_task,
		p.assigned_to, p.event_datetime, p.assigned_to_fullname, p.picture_url,
		p.creation, p.content, p.parent_post, pr.user_image, pr.first_name, pr.last_name
		from tabPost p, tabProfile pr
		where p.parent_post=%s and pr.name = p.owner
		order by p.creation asc""", (post.name,), as_dict=True)
			
	return webnotes.get_template("templates/includes/post_list.html")\
		.render({
			"posts": posts,
			"write": access.get("write"),
			"parent_post": post.name
		})
