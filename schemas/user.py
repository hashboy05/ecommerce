from marshmallow import Schema, fields


class UserSchema(Schema):
    """
    Used for both registration and login request bodies.

    - ``id`` is dump_only (returned, never accepted from the client).
    - ``password`` is load_only (accepted on input, never serialised back
      out in a response, so the hash/plaintext is never leaked).
    """
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
