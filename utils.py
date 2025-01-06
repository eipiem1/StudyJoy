from flask import redirect, session

def login_required(f):
    """
    Decorator used for routes to redirect to the login page if user is not logged in.
    """

    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


