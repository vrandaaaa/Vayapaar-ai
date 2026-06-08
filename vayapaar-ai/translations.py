"""
Vayapaar-AI Global — Translation Dictionary
Supports: English (en), Hindi (hi), Hinglish (hinglish)

Usage in Jinja2 templates:  {{ t.key_name }}
Usage in Python:            TRANSLATIONS[lang]['key_name']
"""

TRANSLATIONS = {
    # ── English ───────────────────────────────────────────────────────────────
    "en": {
        # Navigation
        "dashboard":       "Dashboard",
        "inventory":       "Inventory",
        "pos":             "Point of Sale",
        "finance":         "Finance",
        "customers":       "Customers",
        "settings":        "Settings",
        "logout":          "Logout",

        # Dashboard KPIs
        "total_sales":     "Total Sales",
        "today_sales":     "Today's Sales",
        "gross_profit":    "Gross Profit",
        "net_profit":      "Net Profit",
        "low_stock":       "Low Stock Alert",
        "top_categories":  "Top Selling Categories",

        # Inventory
        "add_product":     "Add Product",
        "edit_product":    "Edit Product",
        "product_name":    "Product Name",
        "sku":             "SKU",
        "barcode":         "Barcode",
        "category":        "Category",
        "cost_price":      "Cost Price",
        "selling_price":   "Selling Price",
        "stock":           "Stock",
        "unit":            "Unit",

        # POS
        "new_sale":        "New Sale",
        "add_to_cart":     "Add to Cart",
        "checkout":        "Checkout",
        "payment_method":  "Payment Method",
        "cash":            "Cash",
        "upi":             "UPI",
        "credit":          "Credit",
        "subtotal":        "Subtotal",
        "discount":        "Discount",
        "tax":             "GST",
        "total":           "Total",
        "complete_sale":   "Complete Sale",

        # Customers / Khata
        "credit_manager":  "Credit Manager (Khata)",
        "outstanding":     "Outstanding",
        "pay_now":         "Record Payment",
        "credit_limit":    "Credit Limit",
        "purchase_history":"Purchase History",

        # Finance
        "revenue":         "Revenue",
        "cogs":            "Cost of Goods Sold",
        "transactions":    "Transactions",

        # Invoice
        "invoice":         "Invoice",
        "print":           "Print",
        "bill_to":         "Bill To",
        "thank_you":       "Thank you for your business!",

        # Auth
        "login":           "Sign In",
        "register":        "Create Account",
        "forgot_password": "Forgot Password",
        "reset_password":  "Reset Password",
        "email":           "Email Address",
        "password":        "Password",
        "confirm_password":"Confirm Password",

        # Common
        "search":          "Search…",
        "save":            "Save",
        "cancel":          "Cancel",
        "edit":            "Edit",
        "delete":          "Delete",
        "archive":         "Archive",
        "welcome":         "Welcome back",
        "dark_mode":       "Dark Mode",
        "no_data":         "No data available",
        "loading":         "Loading…",
        "error":           "An error occurred",
        "success":         "Success",

        # Settings
        "business_profile": "Business Profile",
        "business_name":    "Business Name",
        "business_type":    "Business Type",
        "upi_id":           "UPI ID",
        "phone":            "Phone Number",
        "address":          "Address",
        "gstin":            "GSTIN",
        "update_profile":   "Update Profile",
    },

    # ── Hindi ─────────────────────────────────────────────────────────────────
    "hi": {
        # Navigation
        "dashboard":       "डैशबोर्ड",
        "inventory":       "इन्वेंटरी",
        "pos":             "बिक्री केंद्र",
        "finance":         "वित्त",
        "customers":       "ग्राहक",
        "settings":        "सेटिंग्स",
        "logout":          "लॉग आउट",

        # Dashboard KPIs
        "total_sales":     "कुल बिक्री",
        "today_sales":     "आज की बिक्री",
        "gross_profit":    "सकल लाभ",
        "net_profit":      "शुद्ध लाभ",
        "low_stock":       "कम स्टॉक चेतावनी",
        "top_categories":  "शीर्ष श्रेणियां",

        # Inventory
        "add_product":     "उत्पाद जोड़ें",
        "edit_product":    "उत्पाद संपादित करें",
        "product_name":    "उत्पाद का नाम",
        "sku":             "SKU कोड",
        "barcode":         "बारकोड",
        "category":        "श्रेणी",
        "cost_price":      "लागत मूल्य",
        "selling_price":   "बिक्री मूल्य",
        "stock":           "स्टॉक",
        "unit":            "इकाई",

        # POS
        "new_sale":        "नई बिक्री",
        "add_to_cart":     "कार्ट में जोड़ें",
        "checkout":        "भुगतान करें",
        "payment_method":  "भुगतान का तरीका",
        "cash":            "नकद",
        "upi":             "UPI",
        "credit":          "उधार",
        "subtotal":        "उप-योग",
        "discount":        "छूट",
        "tax":             "GST",
        "total":           "कुल",
        "complete_sale":   "बिक्री पूरी करें",

        # Customers / Khata
        "credit_manager":  "उधार खाता",
        "outstanding":     "बकाया राशि",
        "pay_now":         "भुगतान दर्ज करें",
        "credit_limit":    "उधार सीमा",
        "purchase_history":"खरीद इतिहास",

        # Finance
        "revenue":         "राजस्व",
        "cogs":            "माल की लागत",
        "transactions":    "लेन-देन",

        # Invoice
        "invoice":         "बिल / रसीद",
        "print":           "प्रिंट करें",
        "bill_to":         "ग्राहक का नाम",
        "thank_you":       "आपके व्यापार के लिए धन्यवाद!",

        # Auth
        "login":           "लॉग इन",
        "register":        "खाता बनाएं",
        "forgot_password": "पासवर्ड भूल गए",
        "reset_password":  "पासवर्ड रीसेट करें",
        "email":           "ईमेल पता",
        "password":        "पासवर्ड",
        "confirm_password":"पासवर्ड की पुष्टि करें",

        # Common
        "search":          "खोजें…",
        "save":            "सहेजें",
        "cancel":          "रद्द करें",
        "edit":            "संपादित करें",
        "delete":          "हटाएं",
        "archive":         "संग्रहित करें",
        "welcome":         "स्वागत है",
        "dark_mode":       "डार्क मोड",
        "no_data":         "कोई डेटा उपलब्ध नहीं",
        "loading":         "लोड हो रहा है…",
        "error":           "कोई त्रुटि हुई",
        "success":         "सफल",

        # Settings
        "business_profile": "व्यापार प्रोफ़ाइल",
        "business_name":    "व्यापार का नाम",
        "business_type":    "व्यापार का प्रकार",
        "upi_id":           "UPI आईडी",
        "phone":            "फोन नंबर",
        "address":          "पता",
        "gstin":            "GSTIN",
        "update_profile":   "प्रोफ़ाइल अपडेट करें",
    },

    # ── Hinglish ──────────────────────────────────────────────────────────────
    "hinglish": {
        # Navigation
        "dashboard":       "Dashboard",
        "inventory":       "Maal-Suchi",
        "pos":             "Bikri Kendra",
        "finance":         "Paisa Hisaab",
        "customers":       "Grahak",
        "settings":        "Settings",
        "logout":          "Bahar Jao",

        # Dashboard KPIs
        "total_sales":     "Total Bikri",
        "today_sales":     "Aaj Ki Bikri",
        "gross_profit":    "Gross Kamai",
        "net_profit":      "Net Kamai",
        "low_stock":       "Maal Khatam Ho Raha Hai",
        "top_categories":  "Best Selling Category",

        # Inventory
        "add_product":     "Naya Maal Jodo",
        "edit_product":    "Maal Badlo",
        "product_name":    "Maal Ka Naam",
        "sku":             "SKU Code",
        "barcode":         "Barcode",
        "category":        "Category",
        "cost_price":      "Khareed Bhav",
        "selling_price":   "Bikri Bhav",
        "stock":           "Maal",
        "unit":            "Naap",

        # POS
        "new_sale":        "Naya Saudaa",
        "add_to_cart":     "Cart Mein Daalo",
        "checkout":        "Bill Banao",
        "payment_method":  "Paisa Kaise Doge",
        "cash":            "Nakad",
        "upi":             "UPI",
        "credit":          "Udhaari",
        "subtotal":        "Sub Total",
        "discount":        "Choot",
        "tax":             "GST",
        "total":           "Kul Paisa",
        "complete_sale":   "Saudaa Pakka Karo",

        # Customers / Khata
        "credit_manager":  "Udhaari Khata",
        "outstanding":     "Baaki Paisa",
        "pay_now":         "Abhi De Do",
        "credit_limit":    "Udhaari Limit",
        "purchase_history":"Puranee Khareed",

        # Finance
        "revenue":         "Kamai",
        "cogs":            "Maal Ki Lagat",
        "transactions":    "Len-Den",

        # Invoice
        "invoice":         "Bill / Raseed",
        "print":           "Chhaapo",
        "bill_to":         "Grahak Ka Naam",
        "thank_you":       "Dhanyawaad! Phir Aana!",

        # Auth
        "login":           "Login Karo",
        "register":        "Account Banao",
        "forgot_password": "Password Bhool Gaye?",
        "reset_password":  "Password Badlo",
        "email":           "Email ID",
        "password":        "Password",
        "confirm_password":"Password Dobara Likho",

        # Common
        "search":          "Dhundho…",
        "save":            "Save Karo",
        "cancel":          "Rehne Do",
        "edit":            "Badlo",
        "delete":          "Hatao",
        "archive":         "Chhupao",
        "welcome":         "Aao Phir Se",
        "dark_mode":       "Dark Mode",
        "no_data":         "Kuch Nahi Mila",
        "loading":         "Aa Raha Hai…",
        "error":           "Kuch Gadbad Ho Gayi",
        "success":         "Ho Gaya!",

        # Settings
        "business_profile": "Dukaan Ki Jankari",
        "business_name":    "Dukaan Ka Naam",
        "business_type":    "Dukaan Ka Type",
        "upi_id":           "UPI ID",
        "phone":            "Phone Number",
        "address":          "Pata",
        "gstin":            "GSTIN",
        "update_profile":   "Jankari Badlo",
    },
}
