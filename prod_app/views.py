from django.shortcuts import render, redirect, get_object_or_404
from prod_app.models import Product
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
import re
from django.db.models import Q, Sum, Count

# Multilingual responses
RESPONSES = {
    'en': {
        'greeting': "Hello! 👋 I'm your Product Management Assistant. I can help you manage your inventory, search products, and answer questions about your store. How can I assist you today?",
        'show_products': "I found {count} products in your inventory:\n{products}",
        'show_products_more': "\n... and {remaining} more products.",
        'no_products': "You don't have any products in your inventory yet. Would you like to add some?",
        'search_prompt': "Please specify what product you're looking for. For example: 'find laptop' or 'search for phone'",
        'search_found': "I found {count} product(s) matching '{term}':\n{products}",
        'search_not_found': "Sorry, I couldn't find any products matching '{term}'. Try a different search term.",
        'most_expensive': "The most expensive product is {name} at Rs {price}",
        'cheapest': "The cheapest product is {name} at Rs {price}",
        'no_products_price': "No products found in inventory.",
        'avg_price': "You have {count} products with an average price of Rs {avg:.2f}",
        'low_stock': "Products running low on stock:\n{products}",
        'all_stock_good': "All products are well stocked!",
        'total_stock': "You have {products} different products with a total of {quantity} items in stock.",
        'in_stock': "Products currently in stock:\n{products}",
        'no_stock': "No products are currently in stock.",
        'add_help': "To add a new product, click on the 'Add New Product' button in the dashboard. You'll need to provide the product name, description, price, and quantity.",
        'update_help': "To update a product, go to the products table and click the 'Edit' button next to the product you want to modify.",
        'delete_help': "To delete a product, click the 'Delete' button next to the product in the table. Please be careful as this action cannot be undone.",
        'help': """I can help you with:
• � Dashboard analytics and statistics
• 📋 Show all products
• 🔍 Search for specific products
• 💰 Check prices and costs
• 📦 Check inventory and stock levels
• ➕ Guide you on adding products
• ✏️ Help with updating products
• 🗑️ Assist with deleting products

Try asking me things like:
• "Show dashboard" or "Analytics"
• "Show me all products"
• "Find laptops"
• "What's the cheapest product?"
• "How many items are in stock?" """,
        'goodbye': "You're welcome! 😊 Feel free to ask me anytime you need help with your products. Have a great day!",
        'error': "I'm not sure I understand that request. Try asking me about products, prices, inventory, or type 'help' to see what I can do!",
        'server_error': 'Sorry, I encountered an error processing your request. Please try again.',
    },
    'hi': {
        'greeting': "नमस्ते! 👋 मैं आपका उत्पाद प्रबंधन सहायक हूं। मैं आपकी इन्वेंटरी का प्रबंधन करने, उत्पादों की खोज करने और आपके स्टोर के बारे में प्रश्नों के जवाब देने में आपकी मदद कर सकता हूं। मैं आपकी कैसे मदद कर सकता हूं?",
        'show_products': "मैंने आपकी इन्वेंटरी में {count} उत्पाद पाए:\n{products}",
        'show_products_more': "\n... और {remaining} और उत्पाद।",
        'no_products': "आपकी इन्वेंटरी में अभी तक कोई उत्पाद नहीं है। क्या आप कुछ जोड़ना चाहेंगे?",
        'search_prompt': "कृपया बताएं कि आप कौन सा उत्पाद ढूंढ रहे हैं। उदाहरण के लिए: 'लैपटॉप ढूंढें' या 'फोन खोजें'",
        'search_found': "मैंने '{term}' से मेल खाने वाले {count} उत्पाद पाए:\n{products}",
        'search_not_found': "क्षमा करें, मैं '{term}' से मेल खाने वाला कोई उत्पाद नहीं ढूंढ सका। कोई दूसरा खोज शब्द आजमाएं।",
        'most_expensive': "सबसे महंगा उत्पाद {name} है, कीमत रु {price}",
        'cheapest': "सबसे सस्ता उत्पाद {name} है, कीमत रु {price}",
        'no_products_price': "इन्वेंटरी में कोई उत्पाद नहीं मिला।",
        'avg_price': "आपके पास {count} उत्पाद हैं जिनकी औसत कीमत रु {avg:.2f} है",
        'low_stock': "कम स्टॉक वाले उत्पाद:\n{products}",
        'all_stock_good': "सभी उत्पाद अच्छी तरह से स्टॉक हैं!",
        'total_stock': "आपके पास {products} अलग-अलग उत्पाद हैं जिनमें कुल {quantity} आइटम हैं।",
        'in_stock': "वर्तमान में स्टॉक में उत्पाद:\n{products}",
        'no_stock': "वर्तमान में कोई उत्पाद स्टॉक में नहीं है।",
        'add_help': "नया उत्पाद जोड़ने के लिए, डैशबोर्ड में 'Add New Product' बटन पर क्लिक करें। आपको उत्पाद का नाम, विवरण, कीमत और मात्रा प्रदान करनी होगी।",
        'update_help': "किसी उत्पाद को अपडेट करने के लिए, उत्पाद की टेबल में उस उत्पाद के बगल में 'Edit' बटन पर क्लिक करें।",
        'delete_help': "किसी उत्पाद को हटाने के लिए, टेबल में उत्पाद के बगल में 'Delete' बटन पर क्लिक करें। कृपया सावधान रहें क्योंकि यह क्रिया वापस नहीं की जा सकती।",
        'help': """मैं आपकी इन मदों में मदद कर सकता हूं:
• � डैशबोर्ड विश्लेषण और आंकड़े
• 📋 सभी उत्पाद दिखाएं
• 🔍 विशिष्ट उत्पाद खोजें
• 💰 कीमतें और लागत जांचें
• 📦 इन्वेंटरी और स्टॉक स्तर जांचें
• ➕ उत्पाद जोड़ने में मार्गदर्शन
• ✏️ उत्पाद अपडेट करने में मदद
• 🗑️ उत्पाद हटाने में सहायता

ऐसी बातें पूछने की कोशिश करें:
• "डैशबोर्ड दिखाएं" या "विश्लेषण"
• "मुझे सभी उत्पाद दिखाएं"
• "लैपटॉप ढूंढें"
• "सबसे सस्ता उत्पाद क्या है?"
• "कितने आइटम स्टॉक में हैं?" """,
        'goodbye': "आपका स्वागत है! 😊 जब भी आप अपने उत्पादों के बारे में मदद चाहें, मुझे बेझिझक पूछें। आपका दिन शुभ हो!",
        'error': "मुझे यकीन नहीं है कि मैं इस अनुरोध को समझता हूं। उत्पादों, कीमतों, इन्वेंटरी के बारे में पूछने की कोशिश करें या 'help' टाइप करें कि मैं क्या कर सकता हूं!",
        'server_error': 'क्षमा करें, आपके अनुरोध को प्रोसेस करने में मुझे एक त्रुटि हुई। कृपया पुनः प्रयास करें।',
    },
    'mr': {
        'greeting': "नमस्कार! 👋 मी तुमचा उत्पाद व्यवस्थापन सहायक आहे. मी तुमच्या इन्वेंटरीचे व्यवस्थापन करण्यात, उत्पादांची शोध घेण्यात आणि तुमच्या स्टोरबद्दलच्या प्रश्नांची उत्तरे देण्यात तुम्हाला मदत करू शकतो. मी तुम्हाला कशी मदत करू शकतो?",
        'show_products': "मला तुमच्या इन्वेंटरीमध्ये {count} उत्पाद सापडली:\n{products}",
        'show_products_more': "\n... आणि {remaining} अधिक उत्पाद.",
        'no_products': "तुमच्या इन्वेंटरीमध्ये अद्याप कोणतेही उत्पाद नाहीत. तुम्हाला काही जोडायचे आहे का?",
        'search_prompt': "कृपया सांगा की तुम्हाला कोणते उत्पाद शोधायचे आहे. उदाहरणार्थ: 'लॅपटॉप शोधा' किंवा 'फोन शोधा'",
        'search_found': "मला '{term}' शी जुळणारे {count} उत्पाद सापडले:\n{products}",
        'search_not_found': "क्षमस्व, मला '{term}' शी जुळणारे कोणतेही उत्पाद सापडले नाहीत. दुसरे शोध शब्द वापरून पहा.",
        'most_expensive': "सर्वात महाग उत्पाद {name} आहे, किंमत रु {price}",
        'cheapest': "सर्वात स्वस्त उत्पाद {name} आहे, किंमत रु {price}",
        'no_products_price': "इन्वेंटरीमध्ये कोणतेही उत्पाद सापडले नाहीत.",
        'avg_price': "तुमच्याकडे {count} उत्पाद आहेत ज्यांची सरासरी किंमत रु {avg:.2f} आहे",
        'low_stock': "कमी स्टॉक असलेली उत्पाद:\n{products}",
        'all_stock_good': "सर्व उत्पाद चांगल्या प्रकारे स्टॉक आहेत!",
        'total_stock': "तुमच्याकडे {products} वेगवेगळी उत्पाद आहेत ज्यामध्ये एकूण {quantity} आयटम आहेत.",
        'in_stock': "सध्या स्टॉकमध्ये असलेली उत्पाद:\n{products}",
        'no_stock': "सध्या कोणतेही उत्पाद स्टॉकमध्ये नाहीत.",
        'add_help': "नवीन उत्पाद जोडण्यासाठी, डॅशबोर्डमध्ये 'Add New Product' बटनावर क्लिक करा. तुम्हाला उत्पादाचे नाव, वर्णन, किंमत आणि प्रमाण प्रदान करावे लागेल.",
        'update_help': "काही उत्पाद अपडेट करण्यासाठी, उत्पादांच्या टेबलमध्ये त्या उत्पादाच्या बाजूला 'Edit' बटनावर क्लिक करा.",
        'delete_help': "काही उत्पाद काढण्यासाठी, टेबलमध्ये उत्पादाच्या बाजूला 'Delete' बटनावर क्लिक करा. कृपया काळजी घ्या कारण ही क्रिया परत केली जाऊ शकत नाही.",
        'help': """मी तुम्हाला या गोष्टींमध्ये मदत करू शकतो:
• � डॅशबोर्ड विश्लेषण आणि आकडेवारी
• 📋 सर्व उत्पाद दाखवा
• 🔍 विशिष्ट उत्पाद शोधा
• 💰 किंमती आणि खर्च तपासा
• 📦 इन्वेंटरी आणि स्टॉक स्तर तपासा
• ➕ उत्पाद जोडण्यात मार्गदर्शन
• ✏️ उत्पाद अपडेट करण्यात मदत
• 🗑️ उत्पाद काढण्यात सहाय्य

अशा गोष्टी विचारण्याचा प्रयत्न करा:
• "डॅशबोर्ड दाखवा" किंवा "विश्लेषण"
• "मला सर्व उत्पाद दाखवा"
• "लॅपटॉप शोधा"
• "सर्वात स्वस्त उत्पाद काय आहे?"
• "किती आयटम स्टॉकमध्ये आहेत?" """,
        'goodbye': "तुमचे स्वागत आहे! 😊 जेव्हा तुम्हाला तुमच्या उत्पादांबद्दल मदत हवी असेल, मला निश्चित विचारत रहा. तुमचा दिवस चांगला जावो!",
        'error': "मला खात्री नाही की मी या विनंतीला समजतो. उत्पादांबद्दल, किंमतींबद्दल, इन्वेंटरीबद्दल विचारण्याचा प्रयत्न करा किंवा मी काय करू शकतो ते पाहण्यासाठी 'help' टाइप करा!",
        'server_error': 'क्षमस्व, तुमच्या विनंतीला प्रक्रिया करण्यात मला एक त्रुटी आली. कृपया पुन्हा प्रयत्न करा.',
    }
}

# Language detection patterns
HINDI_WORDS = ['नमस्ते', 'मैं', 'आप', 'है', 'हैं', 'का', 'की', 'के', 'को', 'से', 'पर', 'यह', 'वह', 'क्या', 'कौन', 'कब', 'कहाँ', 'कैसे', 'कितना', 'सब', 'सभी', 'बहुत', 'थोड़ा', 'ज्यादा', 'कम', 'नया', 'पुराना', 'अच्छा', 'बुरा', 'महंगा', 'सस्ता', 'मिल', 'दिखा', 'बताओ', 'देखो', 'खोजो', 'ढूंढो']
MARATHI_WORDS = ['नमस्कार', 'मी', 'तू', 'आहे', 'आहोत', 'का', 'की', 'के', 'को', 'से', 'वर', 'हा', 'ती', 'ते', 'काय', 'कोण', 'केव्हा', 'कुठे', 'कसे', 'किती', 'सर्व', 'सगळे', 'खूप', 'थोडे', 'जास्त', 'कमी', 'नवीन', 'जुना', 'चांगला', 'वाईट', 'महाग', 'स्वस्त', 'मिळ', 'दाखव', 'सांग', 'पहा', 'शोध', 'शोधा']

def detect_language(text):
    """Detect language based on Devanagari script and common words"""
    text = text.lower().strip()

    # Check for Devanagari script
    devanagari_chars = re.findall(r'[\u0900-\u097F]', text)
    if not devanagari_chars:
        return 'en'  # English if no Devanagari characters

    # Count Marathi and Hindi specific words
    marathi_count = sum(1 for word in MARATHI_WORDS if word in text)
    hindi_count = sum(1 for word in HINDI_WORDS if word in text)

    # Additional Marathi-specific patterns
    marathi_patterns = ['का', 'ना', 'ता', 'ते', 'ती', 'ले', 'ला', 'ली', 'ले', 'या', 'ये', 'येत', 'तो', 'तरी', 'पण', 'म्हणून', 'जरी', 'तर', 'की', 'किंवा', 'आणि', 'परंतु']
    marathi_pattern_count = sum(1 for pattern in marathi_patterns if pattern in text)

    # If more Marathi words/patterns, classify as Marathi
    if marathi_count > hindi_count or marathi_pattern_count > 2:
        return 'mr'
    else:
        return 'hi'

# Create your views here.

def home_view(request):
    return render(request,"prod_app/index.html")


def get_All_products(request):
    #ORM Query to get all products
    db = Product.objects.all()
    context = {"data" : db}

    return render(request ,"prod_app/display.html",context)


@login_required
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        category = request.POST.get('category')
        image = request.FILES.get('image')

        # Create new product
        Product.objects.create(
            name=name,
            description=description,
            price=price,
            quantity=quantity,
            category=category,
            image=image
        )
        messages.success(request, 'Product added successfully!')
        return redirect('display')

    return render(request, "prod_app/add.html")


@login_required
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.quantity = request.POST.get('quantity')
        product.category = request.POST.get('category')
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        product.save()
        messages.success(request, 'Product updated successfully!')
        return redirect('display')

    context = {'product': product}
    return render(request, "prod_app/update.html", context)


@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('display')

    context = {'product': product}
    return render(request, "prod_app/delete.html", context)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('display')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'prod_app/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'prod_app/register.html', {'form': form})


@login_required
def chatbot_view(request):
    return render(request, 'prod_app/chatbot.html')


@login_required
def chatbot_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').lower().strip()

            # Detect language
            language = detect_language(user_message)
            responses = RESPONSES[language]

            # Initialize response
            response = {
                'response': '',
                'suggestions': []
            }

            # Product-related queries
            if any(word in user_message for word in ['show', 'list', 'display', 'view', 'all products', 'सभी उत्पाद', 'सर्व उत्पाद', 'दिखा', 'दाखव']):
                products = Product.objects.all()
                if products.exists():
                    product_list = [f"{p.name} (Rs {p.price}, {p.quantity} in stock)" for p in products[:5]]
                    response_text = responses['show_products'].format(
                        count=products.count(),
                        products="\n".join(f"• {p}" for p in product_list)
                    )
                    if products.count() > 5:
                        response_text += responses['show_products_more'].format(remaining=products.count() - 5)
                    response['response'] = response_text
                else:
                    response['response'] = responses['no_products']

            elif any(word in user_message for word in ['search', 'find', 'look for', 'खोज', 'ढूंढ', 'शोध']) and ('product' in user_message or 'item' in user_message or 'उत्पाद' in user_message or 'वस्तु' in user_message):
                # Extract product name from query
                product_name = re.search(r'(?:search|find|look for|खोज|ढूंढ|शोध)\s+(?:a\s+)?(?:product|item|उत्पाद|वस्तु)?\s*(?:called|named|नाम|नाव)?\s*["\']?([^"\']+)["\']?', user_message)
                if product_name:
                    search_term = product_name.group(1).strip()
                    products = Product.objects.filter(
                        Q(name__icontains=search_term) |
                        Q(description__icontains=search_term)
                    )
                    if products.exists():
                        product_list = [f"{p.name}: Rs {p.price} ({p.quantity} in stock)" for p in products]
                        response['response'] = responses['search_found'].format(
                            count=products.count(),
                            term=search_term,
                            products="\n".join(f"• {p}" for p in product_list)
                        )
                    else:
                        response['response'] = responses['search_not_found'].format(term=search_term)
                else:
                    response['response'] = responses['search_prompt']

            elif any(word in user_message for word in ['price', 'cost', 'expensive', 'cheap', 'कीमत', 'महंगा', 'सस्ता', 'किंमत', 'महाग', 'स्वस्त']):
                if 'highest' in user_message or 'most expensive' in user_message or 'सबसे महंगा' in user_message or 'सर्वात महाग' in user_message:
                    product = Product.objects.order_by('-price').first()
                    if product:
                        response['response'] = responses['most_expensive'].format(name=product.name, price=product.price)
                    else:
                        response['response'] = responses['no_products_price']
                elif 'lowest' in user_message or 'cheapest' in user_message or 'सबसे सस्ता' in user_message or 'सर्वात स्वस्त' in user_message:
                    product = Product.objects.order_by('price').first()
                    if product:
                        response['response'] = responses['cheapest'].format(name=product.name, price=product.price)
                    else:
                        response['response'] = responses['no_products_price']
                else:
                    products = Product.objects.all()
                    if products.exists():
                        avg_price = sum(p.price for p in products) / products.count()
                        response['response'] = responses['avg_price'].format(count=products.count(), avg=avg_price)
                    else:
                        response['response'] = responses['no_products_price']

            elif any(word in user_message for word in ['stock', 'quantity', 'inventory', 'available', 'स्टॉक', 'मात्रा', 'इन्वेंटरी', 'उपलब्ध']):
                if 'low' in user_message or 'out' in user_message or 'कम' in user_message:
                    low_stock = Product.objects.filter(quantity__lte=5)
                    if low_stock.exists():
                        product_list = [f"{p.name}: {p.quantity} left" for p in low_stock]
                        response['response'] = responses['low_stock'].format(
                            products="\n".join(f"• {p}" for p in product_list)
                        )
                    else:
                        response['response'] = responses['all_stock_good']
                elif 'total' in user_message or 'count' in user_message or 'कुल' in user_message or 'मोजणी' in user_message:
                    total_products = Product.objects.count()
                    total_quantity = Product.objects.aggregate(total=Sum('quantity'))['total'] or 0
                    response['response'] = responses['total_stock'].format(products=total_products, quantity=total_quantity)
                else:
                    products = Product.objects.filter(quantity__gt=0)
                    if products.exists():
                        in_stock = [f"{p.name}: {p.quantity}" for p in products[:5]]
                        response['response'] = responses['in_stock'].format(
                            products="\n".join(f"• {p}" for p in in_stock)
                        )
                    else:
                        response['response'] = responses['no_stock']

            elif any(word in user_message for word in ['add', 'create', 'new product', 'जोड़', 'बना', 'नया उत्पाद', 'नवीन उत्पाद']):
                response['response'] = responses['add_help']
                if language == 'en':
                    response['suggestions'] = ['add product', 'create product', 'new item']
                elif language == 'hi':
                    response['suggestions'] = ['उत्पाद जोड़ें', 'नया उत्पाद बनाएं', 'आइटम जोड़ें']
                else:  # Marathi
                    response['suggestions'] = ['उत्पाद जोडा', 'नवीन उत्पाद तयार करा', 'आयटम जोडा']

            elif any(word in user_message for word in ['update', 'edit', 'modify', 'अपडेट', 'संपादित', 'बदल']):
                response['response'] = responses['update_help']
                if language == 'en':
                    response['suggestions'] = ['edit product', 'update item', 'modify product']
                elif language == 'hi':
                    response['suggestions'] = ['उत्पाद संपादित करें', 'आइटम अपडेट करें', 'उत्पाद बदलें']
                else:  # Marathi
                    response['suggestions'] = ['उत्पाद संपादित करा', 'आयटम अपडेट करा', 'उत्पाद बदला']

            elif any(word in user_message for word in ['delete', 'remove', 'erase', 'हटा', 'मिटा', 'काढा']):
                response['response'] = responses['delete_help']
                if language == 'en':
                    response['suggestions'] = ['delete product', 'remove item']
                elif language == 'hi':
                    response['suggestions'] = ['उत्पाद हटाएं', 'आइटम हटाएं']
                else:  # Marathi
                    response['suggestions'] = ['उत्पाद काढा', 'आयटम काढा']

            elif any(word in user_message for word in ['dashboard', 'analytics', 'statistics', 'stats', 'report', 'डैशबोर्ड', 'विश्लेषण', 'आकडेवारी']):
                total_products = Product.objects.count()
                total_value = Product.objects.aggregate(total=Sum('price'))['total'] or 0
                low_stock = Product.objects.filter(quantity__lte=5).count()
                categories = Product.objects.values('category').distinct().count()

                response['response'] = f"""📊 Here's your inventory overview:

• 📦 Total Products: {total_products}
• 💰 Total Value: Rs {total_value:.2f}
• ⚠️ Low Stock Items: {low_stock}
• 📂 Product Categories: {categories}

You can view detailed charts and analytics on the Dashboard page!"""

                if language == 'hi':
                    response['response'] = f"""📊 आपकी इन्वेंटरी का अवलोकन:

• 📦 कुल उत्पाद: {total_products}
• 💰 कुल मूल्य: रु {total_value:.2f}
• ⚠️ कम स्टॉक आइटम: {low_stock}
• 📂 उत्पाद श्रेणियां: {categories}

डैशबोर्ड पेज पर विस्तृत चार्ट और विश्लेषण देख सकते हैं!"""
                elif language == 'mr':
                    response['response'] = f"""📊 तुमच्या इन्वेंटरीचा आढावा:

• 📦 एकूण उत्पाद: {total_products}
• 💰 एकूण मूल्य: रु {total_value:.2f}
• ⚠️ कमी स्टॉक आयटम: {low_stock}
• 📂 उत्पाद श्रेणी: {categories}

डॅशबोर्ड पेजवर तपशीलवार चार्ट आणि विश्लेषण पाहू शकता!"""

            elif any(word in user_message for word in ['total products', 'कुल उत्पाद', 'एकूण उत्पाद']):
                total = Product.objects.count()
                response['response'] = f"You have {total} products in your inventory."
                if language == 'hi':
                    response['response'] = f"आपकी इन्वेंटरी में {total} उत्पाद हैं।"
                elif language == 'mr':
                    response['response'] = f"तुमच्या इन्वेंटरीमध्ये {total} उत्पाद आहेत।"

            elif any(word in user_message for word in ['help', 'commands', 'what can you do', 'मदद', 'कमांड', 'क्या कर सकते', 'सहाय्य', 'काय करू शकता']):
                response['response'] = responses['help']

            elif any(word in user_message for word in ['hello', 'hi', 'hey', 'greetings', 'नमस्ते', 'नमस्कार', 'हाय']):
                response['response'] = responses['greeting']

            elif any(word in user_message for word in ['bye', 'goodbye', 'see you', 'thanks', 'अलविदा', 'धन्यवाद', 'नमस्ते', 'पुन्हा भेटू']):
                response['response'] = responses['goodbye']

            else:
                # Default response for unrecognized queries
                response['response'] = responses['error']
                if language == 'en':
                    response['suggestions'] = ['show products', 'help', 'search product', 'check stock']
                elif language == 'hi':
                    response['suggestions'] = ['उत्पाद दिखाएं', 'मदद', 'उत्पाद खोजें', 'स्टॉक जांचें']
                else:  # Marathi
                    response['suggestions'] = ['उत्पाद दाखवा', 'सहाय्य', 'उत्पाद शोधा', 'स्टॉक तपासा']

            return JsonResponse(response)

        except Exception as e:
            # Detect language for error response
            user_message = data.get('message', '') if 'data' in locals() else ''
            language = detect_language(user_message)
            return JsonResponse({
                'response': RESPONSES[language]['server_error'],
                'suggestions': ['help', 'show products'] if language == 'en' else (['मदद', 'उत्पाद दिखाएं'] if language == 'hi' else ['सहाय्य', 'उत्पाद दाखवा'])
            })

    return JsonResponse({'error': 'Invalid request method'})


@login_required

def dashboard_view(request):
    # Get dashboard statistics
    total_products = Product.objects.count()
    total_value = Product.objects.aggregate(total=Sum('price'))['total'] or 0
    low_stock_products = Product.objects.filter(quantity__lte=5).count()
    out_of_stock_products = Product.objects.filter(quantity=0).count()

    # Category-wise count (convert to list for JSON serialization)
    category_counts = list(Product.objects.values('category').annotate(
        count=Count('id'),
        total_value=Sum('price')
    ).order_by('-count'))

    # Price ranges for chart (already a list)
    price_ranges = [
        {'range': '0-500', 'count': Product.objects.filter(price__lt=500).count()},
        {'range': '500-1000', 'count': Product.objects.filter(price__gte=500, price__lt=1000).count()},
        {'range': '1000-5000', 'count': Product.objects.filter(price__gte=1000, price__lt=5000).count()},
        {'range': '5000+', 'count': Product.objects.filter(price__gte=5000).count()},
    ]

    # Recent products (last 5)
    recent_products = Product.objects.order_by('-created_at')[:5]

    context = {
        'total_products': total_products,
        'total_value': total_value,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'category_counts': category_counts,
        'price_ranges': price_ranges,
        'recent_products': recent_products,
    }

    return render(request, 'prod_app/dashboard.html', context)