
def return_error_param(e,error_attr):
    if error_attr=="status_code":
        return e.status_code if hasattr(e,error_attr) else 500
    if error_attr=="detail":
        return e.detail if hasattr(e,error_attr) else "Error server"