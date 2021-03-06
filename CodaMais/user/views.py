# standard library
import logging
import hashlib
import datetime
import random

# Django
from django.shortcuts import (
    render, redirect, render_to_response, get_object_or_404
)

from django.core.mail import send_mail
from django.utils import timezone
from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required

# local Django
from .forms import (
    UserRegisterForm, UserLoginForm, UserEditForm, RecoverPasswordForm, ConfirmPasswordForm
)
from .models import(
    User, UserProfile, RecoverPasswordProfile
)
from . import constants

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(constants.PROJECT_NAME)


def register_view(request):
    form = UserRegisterForm(request.POST or None)
    logger.debug("Rendering Register Page.")
    if form.is_valid():
        logger.debug("Register form is valid.")
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        username = form.cleaned_data.get('username')
        first_name = form.cleaned_data.get('first_name')
        User.objects.create_user(email=email, password=password,
                                 username=username, first_name=first_name)

        # Prepare the information needed to send the account verification
        # email.
        salt = hashlib.sha1(str(random.random()).
                            encode('utf-8')).hexdigest()[:5]
        activation_key = hashlib.sha1(str(salt+email).
                                      encode('utf‌​-8')).hexdigest()
        key_expires = datetime.datetime.today() + datetime.timedelta(2)

        user = User.objects.get(username=username)

        new_profile = UserProfile(user=user, activation_key=activation_key,
                                  key_expires=key_expires)
        new_profile.save()

        # Send account confirmation email.
        email_subject = (constants.EMAIL_CONFIRMATION_SUBJECT)
        email_body = constants.EMAIL_CONFIRMATION_BODY % (username,
                                                          activation_key)

        send_mail(email_subject, email_body, constants.CODAMAIS_EMAIL, [email],
                  fail_silently=False)

        return render(request, "register_sucess.html")

    else:
        logger.debug("Register form was invalid.")

    return render(request, "register_form.html", {"form": form})


def register_confirm(request, activation_key):
    # Verify if user is already confirmed.
    if request.user.is_authenticated():
        HttpResponse('Conta ja confirmada')
    else:
        # Nothing to do
        pass

    # Check if activation token is valid, if not valid return an 404 error.
    user_profile = get_object_or_404(UserProfile,
                                     activation_key=activation_key)

    # Verifies if the activation token has expired and if so renders the html
    # of expired registration.

    if user_profile.key_expires < timezone.now():
        user_profile.delete()
        return HttpResponse("Tempo para confirmar conta expirou.Crie novamente")
    else:
        # Nothing to do.
        pass

    # If the token has not expired, the user is activated and the
    # confirmation html is displayed.

    user = user_profile.user
    user.is_active = True
    user.save()

    return render_to_response('confirmed_account.html')


def login_view(request):
    logger.debug("Rendering login page.")
    form = UserLoginForm(request.POST or None)

    if request.method == "POST":
        logger.debug("Login View request is POST.")
        if form.is_valid():
            logger.debug("Login form is valid.")

            email = request.POST['email']
            password = request.POST['password']
            user = auth.authenticate(email=email, password=password)

            if user is not None:
                if user.is_active:
                    auth.login(request, user)
                    # TODO(João) Change this return to user page html
                    return render_to_response('login/login_success.html')
                else:
                    # Nothing to do.
                    pass
            else:
                # Nothing to do.
                pass
        else:
            # Nothing to do.
            logger.debug("Login form is invalid.")
            pass
    else:
        logger.debug("Login View request is GET.")
        pass

    # TODO(João) Change this render to landpage
    return render(request, "login/login_form.html", {"form": form})


# TODO(João) Change this return to landpage.
def logout_view(request):
    logger.info("User Logout.")
    auth.logout(request)
    return render(request, "login/login_form.html", {})


# This function will be called when user forgot his password, and ask a new.
def recover_password(request):
    form = RecoverPasswordForm(request.POST or None)
    logger.info("Rendering Recover Password Page.")
    button_text = constants.CONFIRM_BUTTON

    if form.is_valid():

        email = form.cleaned_data.get('email')

        try:
            user = User.objects.get(email=email)
        except:
            logger.info("This email don't exist in database.")
            return render(request, 'recover_password.html', {"form": form, "buttonText:": button_text})

        try:
            # Prepare informations to send email
            salt = hashlib.sha1(str(random.random()).
                                encode('utf-8')).hexdigest()[:5]
            activation_key = hashlib.sha1(str(salt+email).
                                          encode('utf‌​-8')).hexdigest()
            key_expires = datetime.datetime.today() + datetime.timedelta(2)

            new_profile = RecoverPasswordProfile(user=user,
                                                 activation_key=activation_key,
                                                 key_expires=key_expires)
            new_profile.save()

            # Send password recovery.
            email_subject = (constants.PASSWORD_RECOVER_SUBJECT)
            email_body = constants.PASSWORD_RECOVER_BODY % (user.username,
                                                            activation_key)

            send_mail(email_subject, email_body, constants.CODAMAIS_EMAIL, [email],
                      fail_silently=False)

            logger.info("Recover password email sended.")
        except:
            # TODO(João) Add some mechanism to show error message to user.
            logger.info("This email already asked another password.")
            return render(request, 'recover_password.html', {"form": form, "buttonText:": button_text})
    else:
        # Nothing to do.
        pass

    return render(request, 'recover_password.html', {"form": form, "button_text:": button_text})


# This function will be called when user click in link sended in his email.
def recover_password_confirm(request, activation_key):

    form = ConfirmPasswordForm(request.POST or None)
    title = constants.PASSWORD_RECOVER
    button_text = constants.PASSWORD_CHANGE
    user_profile = get_object_or_404(RecoverPasswordProfile,
                                     activation_key=activation_key)

    user = user_profile.user

    if user_profile.key_expires < timezone.now():
        logger.info("Time do change password expired.")
        user_profile.delete()
        return HttpResponse("Tempo para mudar a senha expirou!Peça novamente")
    else:
        # Nothing to do.
        pass

    # If the key has not expired, the user can change password.

    if request.method == "POST":
        if form.is_valid():
            user.set_password(form.cleaned_data.get('password'))
            user.save()
            user_profile.delete()
            return redirect('/')
        else:
            # Nothing to do.
            pass
    else:
        # Nothing to do.
        pass
    # TODO(João) Change this html to "beautiful way".
    return render(request, "confirmpassword.html", {"form": form, "title": title, "button_text": button_text})


def profile_view(request, username):

    editable_profile = False  # Variable to define if user will see a button to edit his profile page.

    if request.method == "GET":
        user = User.objects.get(username=username)
        # Check if logged user is visiting his own profile page.
        if request.user.username == user.username:
            logger.debug("Profile page should be editable")
            editable_profile = True
        else:
            logger.debug("Profile page shouldn't be editable.")
            # Nothing to do.
    else:
        logger.debug("Profile view request: POST")
        user = User()

    logger.debug("Profile page is editable? " + str(editable_profile))
    return render(request, 'profile.html', {'user': user, 'editable_profile': editable_profile})


@login_required
def edit_profile_view(request, username):
    logger.debug("Rendering edit profile page.")
    user = User.objects.get(username=username)
    form = UserEditForm(request.POST or None, request.FILES or None)

    if request.user.username == user.username:
        if request.method == "POST":
            logger.debug("Edit profile view request is POST.")
            if form.is_valid():
                logger.debug("Valid edit form.")
                password = form.cleaned_data.get('password')
                first_name = form.cleaned_data.get('first_name')
                new_user_image = request.FILES.get('user_image', None)

                # User changed password.
                if len(password) != constants.NULL_FIELD:
                    user.password = password
                # User did not change password.
                else:
                    pass
                # User changed first name.
                if len(first_name) != constants.NULL_FIELD:
                    user.first_name = first_name
                # User did not change first name.
                else:
                    pass
                # User changed user image.
                if new_user_image is not None:
                    user.user_image = new_user_image
                # User did not change user image.
                else:
                    pass

                user.save()

                return HttpResponse("Data altered.")
            else:
                logger.debug("Invalid edit form.")
                pass
        else:
            logger.debug("Edit profile view request is GET.")
            pass
    else:
        logger.debug("User can't edit other users information.")
        return HttpResponse("Oops! You don't have acess to this page.")
    return render(request, 'edit_profile_form.html', {'form': form, 'user': user})
