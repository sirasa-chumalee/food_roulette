"""Gemini calls, kept in one place so the rest of the app never imports the SDK.

Two steps of the sandwich live here (DESIGN §6): `extract` reads the user's
message *before* any restaurant exists, and `narrate` writes prose *after* the
filter has already chosen. Neither one may decide what is safe to eat.
"""
