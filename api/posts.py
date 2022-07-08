from flask import jsonify, request, g, abort
from sqlalchemy import null

from api import api
from db.shared import db
from db.models.user_post import UserPost
from db.models.post import Post

from db.utils import row_to_dict
from middlewares import auth_required


@api.post("/posts")
@auth_required
def posts():
    # validation
    user = g.get("user")
    if user is None:
        return abort(401)

    data = request.get_json(force=True)
    text = data.get("text", None)
    tags = data.get("tags", None)
    
    if text is None:
        return jsonify({"error": "Must provide text for the new post"}), 400

    # Create new post
    post_values = {"text": text}
    if tags:
        post_values["tags"] = tags

    post = Post(**post_values)
    db.session.add(post)
    db.session.commit()

    user_post = UserPost(user_id=user.id, post_id=post.id)
    db.session.add(user_post)
    db.session.commit()

    return row_to_dict(post), 200

@api.route("/posts", methods=["GET"])
def getPosts():
    data = request.get_json(force=True)
    authorIDs = data.get("authorIDs", None)

    if authorIDs is None:
        return jsonify({"error": "Must provide at least one author ID"}), 400

    authorIDs = authorIDs.split(",")
    posts = [Post().get_posts_by_user_id(authorID) for authorID in authorIDs]
    posts = set([post for postsList in posts for post in postsList])
   
    sortBy = data.get("sortBy", None)
    direction = data.get("direction", None)

    if direction not in [None, "asc", "desc"]:
        return jsonify({"error": "direction can be 'asc' or 'desc' or nothing"}), 400

    direction = (direction is not None) and (direction == "desc")

    if sortBy is not None:
        sortBy = sortBy.lower()

        if sortBy == "popularity":
            posts = sorted(posts, key=lambda x: x.popularity, reverse=direction)
        elif sortBy == "reads":
            posts = sorted(posts, key=lambda x: x.reads, reverse=direction)
        elif sortBy == "likes":
            posts = sorted(posts, key=lambda x: x.likes, reverse=direction)
        elif sortBy == "id":
            posts = sorted(posts, key=lambda x: x.id, reverse=direction)
        else:
            return jsonify({"error": "sortBy cannot be" + sortBy + ", it should be 'read', 'popularity', 'likes' or 'id'"}), 400
    else: 
        posts = sorted(posts, key=lambda x: x.id, reverse=direction)

    return jsonify({"posts": [row_to_dict(post) for post in posts]})

@api.route("/posts/<int:postId>", methods=["PATCH"])
@auth_required
def updatePost(postId):
    # validation
    user = g.get("user")
    if user is None:
        return abort(401)

    post = Post().get_post(postId)

    if post is None:
        return jsonify({"error": "Post with id {} doesn't exist".format(postId)}), 400

    if user not in post.users:
        return jsonify({"error": "You are not authorized to update this post"})

    data = request.get_json(force=True)
    authorIds = data.get("authorIds", [])
    tags = data.get("tags", [])
    text = data.get("text", None)

    for authorId in authorIds:
        if authorId not in [user.id for user in post.users]:
            user_post = UserPost(user_id=authorId, post_id=post.id)
            db.session.add(user_post)
            db.session.commit()
    
    for id in [user.id for user in post.users]:
        if id not in authorIds:
            UserPost.query.filter_by(user_id=id, post_id=post.id).delete()
            db.session.commit()

    if tags:
        post.tags = set(tags)
        db.session.commit()

    if text is not None:
        post.text = text
        db.session.commit()

    authorIds = [user.id for user in post.users]
    post = row_to_dict(post)
    post.update({"authorIds": authorIds})

    return jsonify({"post": post})