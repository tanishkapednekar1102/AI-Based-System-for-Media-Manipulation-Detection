from nicegui import ui, app

from backend.database.users import register_user, authenticate_user
from frontend.components.layout import STYLE_BG, STYLE_CARD, render_public_header

def register_auth_routes():
    @ui.page('/register')
    def page_register():
        ui.query('body').style(STYLE_BG)
        render_public_header()

        with ui.column().classes("w-full max-w-md mx-auto px-6 py-16 gap-6 items-center"):
            with ui.card().style(STYLE_CARD).classes("w-full p-8 gap-4"):
                ui.label("Create New Account").classes("text-2xl font-bold text-white text-center")
                ui.label("Register to access media detection and history").classes("text-xs text-gray-400 text-center")

                full_name = ui.input("Full Name").props("outlined dark color=cyan icon=person").classes("w-full")
                email = ui.input("Email Address").props("outlined dark color=cyan icon=email").classes("w-full")
                password = ui.input("Password", password=True).props("outlined dark color=cyan icon=lock").classes("w-full")
                confirm_pwd = ui.input("Confirm Password", password=True).props("outlined dark color=cyan icon=lock").classes("w-full")

                def handle_register():
                    if password.value != confirm_pwd.value:
                        ui.notify("Passwords do not match.", type="negative")
                        return

                    success, msg = register_user(full_name.value, email.value, password.value)
                    if success:
                        ui.notify(msg, type="positive")
                        ui.navigate.to('/login')
                    else:
                        ui.notify(msg, type="negative")

                ui.button("Register Account", on_click=handle_register).props("unelevated color=cyan-7 text-color=white").classes("w-full py-3 rounded-lg font-bold mt-2")
                with ui.row().classes("justify-center text-xs text-gray-400 mt-2"):
                    ui.label("Already have an account?")
                    ui.link("Login here", "/login").classes("text-cyan-400 font-semibold no-underline")

    @ui.page('/login')
    def page_login():
        ui.query('body').style(STYLE_BG)
        render_public_header()

        with ui.column().classes("w-full max-w-md mx-auto px-6 py-16 gap-6 items-center"):
            with ui.card().style(STYLE_CARD).classes("w-full p-8 gap-4"):
                ui.label("User Login").classes("text-2xl font-bold text-white text-center")
                ui.label("Sign in to access forensic detection dashboard").classes("text-xs text-gray-400 text-center")

                email = ui.input("Email Address").props("outlined dark color=cyan icon=email").classes("w-full")
                password = ui.input("Password", password=True).props("outlined dark color=cyan icon=lock").classes("w-full")

                def handle_login():
                    success, msg, user_info = authenticate_user(email.value, password.value)
                    if success and user_info:
                        app.storage.user['user'] = user_info
                        ui.notify(msg, type="positive")
                        ui.navigate.to('/dashboard')
                    else:
                        ui.notify(msg, type="negative")

                ui.button("Login to Dashboard", on_click=handle_login).props("unelevated color=cyan-7 text-color=white").classes("w-full py-3 rounded-lg font-bold mt-2")
                with ui.row().classes("justify-center text-xs text-gray-400 mt-2"):
                    ui.label("Don't have an account?")
                    ui.link("Register here", "/register").classes("text-cyan-400 font-semibold no-underline")

    @ui.page('/logout')
    def page_logout():
        app.storage.user.clear()
        ui.notify("Logged out successfully.", type="info")
        ui.navigate.to('/')
