
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect,render_to_response

from django.contrib.auth import login, authenticate,logout
from django.contrib.auth.decorators import login_required

from .forms import SignupForm, LoginForm, EditProfileForm

from django.contrib.auth.models import User
from django.contrib import messages

from django.views import generic
from django.utils.decorators import method_decorator

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import send_mail
from auction.settings import EMAIL_HOST_USER
from .models import MyProfile
from .forms import ProductForm
from .models import Product, Bids
from django.views.generic import DetailView,FormView,ListView
from django.views.generic.edit import FormMixin
from .forms import BidsForm
from django.views import View
import json
from django.db.models import Q
from django.template import RequestContext
from django.http import JsonResponse



def home(request):
    return render(request, 'app/home.html')

# Signup using Email Verification
def signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            form = SignupForm(request.POST)
            if form.is_valid():
                    user = form.save(commit=False)
                    user.is_active = False
                    user.save()
                    current_site = get_current_site(request)
                    subject = 'Your Online-Auction Email Verification is here..'
                    message = render_to_string('app/acc_active_email.html', {

                        'user': user,
                        'domain': current_site.domain,
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode,
                        'token': account_activation_token.make_token(user),
                    })
                    from_mail = EMAIL_HOST_USER
                    to_mail = [user.email]
                    send_mail(subject, message, from_mail, to_mail, fail_silently=False)
                    messages.success(request, 'Confirm your email to complete registering with ONLINE-AUCTION.')
                    return redirect('home')
        else:
            form = SignupForm()
        return render(request, 'app/signup.html', {'form': form})


#account activation function
def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, 'EMAIL VERIFIED!!!! HURRAY....')
        return redirect('home')
    else:
        return HttpResponse('Activation Link is Invalid. Try once more...')


def logout_view(request):
    logout(request)
    messages.success(request, 'You are  logged out')
    return redirect('home')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return render(request, 'app/home.html')
            else:
                return HttpResponse('Please! Verify your Email first')
        else:
            messages.error(request, 'Username or Password is incorrect')
            return redirect('login')

    else:
        form = LoginForm()
    return render(request, 'app/login.html', {'form': form})





@login_required
def profile_view(request):
    return render(request, 'app/profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=request.user.myprofile)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = EditProfileForm(instance=request.user.myprofile)
    return render(request, 'app/edit_profile.html', {'form': form})

# --------------------------------------------------------------------------------------------

# @login_required
# class VisaForm(generic.edit.FormView):
#     form_class = VisaForm
#     template_name = 'templates/visa.html'
#
#     def get(self, request, *args, **kwargs):
#         try:
#             form = self.form_class
#


class BuyerView(ListView):

    template_name = 'app/buyer.html'
    context_object_name = 'product_list'

    def get_queryset(self):
        return Product.objects.order_by('id')






class ProductView(View):

    template_name = 'app/product.html'

    def get(self, request, *args, **kwargs):

        p = Product.objects.get(id=kwargs['pk'])
        form = BidsForm()
        context = {
            'name': p.name,
            'desp': p.desp,
            'start': p.start,
            'minbid': p.minimum_price,
            'end': p.end_date,
            'category': p.category,
            'currentbid': p.current_bid,
            'form': form

        }

        if p.product_sold == 'False':
            return render(request, 'app/product_sold.html', context)
        else:
            return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        p = Product.objects.get(id=kwargs["pk"])

        print(p.name)
        form = BidsForm(request.POST)
        if form.is_valid():
            print(12)
            if p.minimum_price < int((request.POST['bidder_amount'])) and \
                    p.current_bid < int((request.POST['bidder_amount'])):
                p.current_bid = int((request.POST['bidder_amount']))

                print(p.current_bid)
                p.save()


        context = {
            'name': p.name,
            'desp': p.desp,
            'start': p.start,
            'minbid': p.minimum_price,
            'end': p.end_date,
            'category': p.category,
            'currentbid': p.current_bid,
            'form': form
            }

        return render(request, self.template_name, context)

@login_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product_item = form.save(commit=False)
            product_item.seller_id = request.user
            product_item.save()
            return redirect('home')
    else:
        form = ProductForm()
    return render(request, 'app/product_form.html', {'form' : form})




'''
def category_product(request):
    if request.method == "POST":
        form = categoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.save()
            
            return redirect('home')
    else:
        form = categoryForm()
    return render(request, 'app/category_search.html', {'form' : form})


def category_product(request):

    if request.method=="POST":
        item=request.POST['item']
        if item:
            match=Product.objects.filter(Q(name__icontains=item))
            if match:
                return render(request,'app/category_search.html',{'sr':match})

            else:
                messages.error(request,'no results')
        else:
            return HttpResponseRedirect('/category/')

    return render(request,'app/category_search.html',{'Product':Product})

def search_titles(request):

    product = {
        "name":Product.name,
        "category":Product.category
    }
    print(product)

    data = request.GET.get('data')
    
    list = Product.objects.all()
    search = list.filter(name__icontains=data)
    product[(search[i])] =search_user[i]

    return JsonResponse(product)
def search(request, *args, **kwargs):
    data = dict()
    data["foo"] = "bar"
    data["username"] = Product.objects.get(name)
    return JsonResponse(data)
    
 '''
def search(request):
    if request.is_ajax():
        searchText = request.get['searchText']
        print(searchText)
        product = Product.objects.all.filter(name__icontains = searchText)
        result = []
        for k in product:
            item = {}

            item['label'] = k.name
            item['category'] = k.category
            result.append(item)
        return JsonResponse({"results":result})
            #type = 'app/search.html'
        #return HttpResponse(data, type)
'''
def index(request):
    return render(request, "app/search.html")'''
'''
def search(request):
	text = request.args['searchText']


    BRAZIL_STATES = [u"Acre - Rio Branco",
                 u"Alagoas - Maceió",
                 u"Amapá",
                 u"Amazonas - Manaus",
                 u"Bahia - Salvador",
                 u"Ceara - Fortaleza"]

	result =  BRAZIL_STATES[1]
	# return as JSON
	return json.dumps({"results":result})


    else:
        data = 'fail'
    search = 'app/ajax_search.html' '''
'''
class AddProduct(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = ProductForm(request.POST, request.FILES)
        # p = Product.objects.get(id=request.User.id)

        if form.is_valid():
            # product_item = form.save(commit=False).....WTF?
            product_item = form.save(commit=False)
            product_item.seller_id = request.user
            product_item.save()
            return redirect('home')

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        form = ProductForm()
        context = {'form' : form}
        return render(request, 'app/product_form.html', context)

# ---------------------------------------------------------------------------------------------------


class BuyerView(View):

    template_name = 'app/buyer.html'

    def get(self, request, *args, **kwargs):
        context = {
            'product_list': Product.objects.order_by('id'),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        sort_by = request.POST['sort']
        if sort_by == 'new_to_old':
            context = {
                'product_list': Product.objects.order_by('-start'),
            }

        elif sort_by == 'old_to_new':
            context = {
                'product_list': Product.objects.order_by('start'),
            }

        elif sort_by == 'high_to_low':
            context = {
                'product_list': Product.objects.order_by('-current_bid'),
            }

        elif sort_by == 'low_to_high':
            context = {
                'product_list': Product.objects.order_by('current_bid'),
            }
'''
'''
class ProductListed(View):

    template_name = 'app/product_listed.html'

    def get(self, request, *args, **kwargs):
        user_id = request.user
        pr = Product.objects.filter(seller_id=user_id)
        context = {
            'product': pr
            }

        return render(request, self.template_name,context)
        '''
