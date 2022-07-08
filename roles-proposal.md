# Roles Proposal

## What database changes would be required to the starter code to allow for different roles for authors of a blog post? Imagine that we’d want to also be able to add custom roles and change the permission sets for certain roles on the fly without any code changes.

We'd introduce a new table called roles with two columns - **role_name and role_permission** (r, w, rw, rwd, null).

`id  role_name role_permission`
`1   owner     rwd`
`2   editor    rw`
`3   viewer    r`

The id for this table would be a foreign key in the user_post table.
If there doesn't exist a row for a post_id, then the role_id for that row would be by default 1 (owner).

`id  post_id   user_id   role_id`
`5   3         9         1`

Class Role would contain a method to retrieve the role and its permissions by name. 

Class Role could be initialized by passing the role_name and role_permission, and it would create a new role if it doesn't exist. 

## How would you have to change the PATCH route given your answer above to handle roles?

At `/api/posts`, `PATCH` would allow to modify the type of role that a person has, so the response could look like the following:

```bash
{
  "post": {
    "id": 1,  # number
    "authorIds": [1, 5],  # array of numbers
    "roleId": 1 # number
    "role_name": "owner", # string (Included in the response object, not in the Post class)
    "likes": 960,  # number
    "popularity": 0.13,  # number
    "reads": 50361,  # number
    "tags": ["health", "tech"],  # array of strings
    "text": "Some very short blog post text here."  # string
  }
}
```