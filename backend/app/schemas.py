
from marshmallow import Schema, fields, validate, EXCLUDE


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

# ---------- Auth ----------

class RegisterSchema(BaseSchema):
    email = fields.Email(required=True, error_messages={"required": "Email is required"})
    password = fields.String(required=True, validate=validate.Length(min=6, max=128))
    role = fields.String(required=True, validate=validate.OneOf(["student", "employer"]))
    full_name = fields.String(required=False, validate=validate.Length(max=100))
    company_name = fields.String(required=False, validate=validate.Length(max=150))


class LoginSchema(BaseSchema):
    
    email = fields.Email(required=True)
    password = fields.String(required=True)


class ForgotPasswordSchema(BaseSchema):
    email = fields.Email(required=True)


class ResetPasswordSchema(BaseSchema):
    reset_token = fields.String(required=True)
    new_password = fields.String(required=True, validate=validate.Length(min=6, max=128))


# ---------- Students ----------

class UpdateProfileSchema(BaseSchema):
    full_name = fields.String(required=False, validate=validate.Length(max=100))
    phone = fields.String(required=False, validate=validate.Length(max=20))
    university = fields.String(required=False, validate=validate.Length(max=150))
    degree = fields.String(required=False, validate=validate.Length(max=100))
    gpa = fields.Float(required=False, validate=validate.Range(min=0, max=4))
    skills = fields.List(fields.String(), required=False)


# ---------- Internships ----------

class CreateInternshipSchema(BaseSchema):
    title = fields.String(required=True, validate=validate.Length(min=2, max=150))
    description = fields.String(required=True, validate=validate.Length(min=10))
    required_skills = fields.List(fields.String(), required=False)
    location = fields.String(required=False, validate=validate.Length(max=100))
    duration = fields.String(required=False, validate=validate.Length(max=50))
    stipend = fields.String(required=False, validate=validate.Length(max=50))
    deadline = fields.Date(required=False, allow_none=True)


class UpdateInternshipSchema(BaseSchema):
    title = fields.String(required=False, validate=validate.Length(min=2, max=150))
    description = fields.String(required=False, validate=validate.Length(min=10))
    required_skills = fields.List(fields.String(), required=False)
    location = fields.String(required=False, validate=validate.Length(max=100))
    duration = fields.String(required=False, validate=validate.Length(max=50))
    stipend = fields.String(required=False, validate=validate.Length(max=50))
    deadline = fields.Date(required=False, allow_none=True)
    is_active = fields.Boolean(required=False)


# ---------- Matching ----------

class UpdateApplicationStatusSchema(BaseSchema):
    status = fields.String(required=True, validate=validate.OneOf(["pending", "accepted", "rejected"]))


# ---------- Chat ----------

class ChatMessageSchema(BaseSchema):
    message = fields.String(required=True, validate=validate.Length(min=1, max=2000))
    history = fields.List(fields.Dict(), required=False, load_default=list)