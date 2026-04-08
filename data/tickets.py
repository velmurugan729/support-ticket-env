# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Synthetic customer support tickets for the ticket routing environment.

Contains 28 tickets across three difficulty levels:
- 10 easy: obvious single-department issues
- 10 medium: ambiguous tickets that could fit multiple departments
- 8 hard: complex multi-issue tickets requiring reasoning
"""

TICKETS = [
    # EASY TICKETS (10) - obvious single-department issues
    {
        "ticket_id": "E001",
        "subject": "Credit card charge not showing on my account",
        "body": "I was charged $49.99 on my credit card but the payment isn't reflected in my account balance. Please check this billing discrepancy.",
        "customer_tier": "silver",
        "priority": "medium",
        "correct_department": "Billing",
        "difficulty": "easy",
        "adjacent_departments": []
    },
    {
        "ticket_id": "E002",
        "subject": "Application crashes when I click save",
        "body": "Every time I try to save my work in the application, it crashes with error code 0x0000005. This started happening after the last update.",
        "customer_tier": "gold",
        "priority": "high",
        "correct_department": "Technical",
        "difficulty": "easy",
        "adjacent_departments": []
    },
    {
        "ticket_id": "E003",
        "subject": "Package never arrived - tracking shows delivered",
        "body": "My order #12345 was marked as delivered yesterday but I never received it. The tracking says it was left at front door but nothing is there.",
        "customer_tier": "bronze",
        "priority": "high",
        "correct_department": "Shipping",
        "difficulty": "easy",
        "adjacent_departments": []
    },
    {
        "ticket_id": "E004",
        "subject": "I want to return this damaged item",
        "body": "The product I received arrived with a cracked screen. I would like to return it for a full refund. The box was also damaged.",
        "customer_tier": "platinum",
        "priority": "medium",
        "correct_department": "Returns",
        "difficulty": "easy",
        "adjacent_departments": []
    },
    {
        "ticket_id": "E005",
        "subject": "Invoice payment dispute",
        "body": "I received invoice #INV-2024-789 but the amount is incorrect. I was quoted $200 but the invoice shows $250. Please correct this.",
        "customer_tier": "silver",
        "priority": "medium",
        "correct_department": "Billing",
        "difficulty": "easy",
        "adjacent_departments": []
    },
    {
        "ticket_id": "E006",
        "subject": "Login authentication failed repeatedly",
        "body": "I cannot log into my account. I've reset my password three times but keep getting 'authentication failed' error. My username is john_doe123.",
        "customer_tier": "gold",
        "priority": "high",
        "correct_department": "Technical",
        "difficulty": "easy",
        "adjacent_departments": []
    },
    {
        "ticket_id": "E007",
        "subject": "Wrong shipping address on my order",
        "body": "I just placed order #67890 and realized I used my old address. The package is going to the wrong place. Can this be corrected before it ships?",
        "customer_tier": "bronze",
        "priority": "high",
        "correct_department": "Shipping",
        "difficulty": "easy",
        "adjacent_departments": []
    },
    {
        "ticket_id": "E008",
        "subject": "Return label not generating",
        "body": "I'm trying to process a return for order #54321 but the system won't generate a return label. It just spins and then shows an error message.",
        "customer_tier": "silver",
        "priority": "medium",
        "correct_department": "Returns",
        "difficulty": "easy",
        "adjacent_departments": []
    },
    {
        "ticket_id": "E009",
        "subject": "Subscription auto-renewal charge",
        "body": "I was charged for another year of subscription even though I cancelled last month. Please refund this unauthorized charge of $99.",
        "customer_tier": "gold",
        "priority": "high",
        "correct_department": "Billing",
        "difficulty": "easy",
        "adjacent_departments": []
    },
    {
        "ticket_id": "E010",
        "subject": "Website 500 error on checkout page",
        "body": "When I try to complete my purchase, I get a 500 Internal Server Error on the checkout page. This happens every time I try to pay.",
        "customer_tier": "bronze",
        "priority": "high",
        "correct_department": "Technical",
        "difficulty": "easy",
        "adjacent_departments": []
    },

    # MEDIUM TICKETS (10) - ambiguous tickets that could fit multiple departments
    {
        "ticket_id": "M001",
        "subject": "Product stopped working after 2 weeks",
        "body": "The device I purchased stopped working after just two weeks of use. It won't turn on at all. I'd like a replacement or refund.",
        "customer_tier": "silver",
        "priority": "high",
        "correct_department": "Returns",
        "difficulty": "medium",
        "adjacent_departments": ["Technical", "Billing"]
    },
    {
        "ticket_id": "M002",
        "subject": "Charged for item that was out of stock",
        "body": "I was charged for an item that was supposedly out of stock. The order was cancelled but my credit card was still charged $45.",
        "customer_tier": "gold",
        "priority": "medium",
        "correct_department": "Billing",
        "difficulty": "medium",
        "adjacent_departments": ["Shipping", "Returns"]
    },
    {
        "ticket_id": "M003",
        "subject": "App won't let me complete purchase",
        "body": "I'm trying to buy a subscription in the mobile app but the payment keeps failing. I've tried two different cards with no success.",
        "customer_tier": "bronze",
        "priority": "medium",
        "correct_department": "Technical",
        "difficulty": "medium",
        "adjacent_departments": ["Billing"]
    },
    {
        "ticket_id": "M004",
        "subject": "Received wrong item and want exchange",
        "body": "I ordered a blue medium shirt but received a red large one. I need the correct item sent to me. The order number is #98765.",
        "customer_tier": "silver",
        "priority": "medium",
        "correct_department": "Shipping",
        "difficulty": "medium",
        "adjacent_departments": ["Returns"]
    },
    {
        "ticket_id": "M005",
        "subject": "Download link not working after purchase",
        "body": "I purchased the software download but the download link in my confirmation email returns a 404 error. I need access to what I paid for.",
        "customer_tier": "gold",
        "priority": "high",
        "correct_department": "Technical",
        "difficulty": "medium",
        "adjacent_departments": ["Billing"]
    },
    {
        "ticket_id": "M006",
        "subject": "Package damaged in transit - refund request",
        "body": "My package arrived with the box completely crushed and the product inside is damaged. I would like a refund rather than a replacement.",
        "customer_tier": "platinum",
        "priority": "medium",
        "correct_department": "Billing",
        "difficulty": "medium",
        "adjacent_departments": ["Shipping", "Returns"]
    },
    {
        "ticket_id": "M007",
        "subject": "Account locked after payment failure",
        "body": "My account got locked after a payment attempt failed. Now I can't access my subscription or update my payment method. Please help.",
        "customer_tier": "silver",
        "priority": "high",
        "correct_department": "Technical",
        "difficulty": "medium",
        "adjacent_departments": ["Billing"]
    },
    {
        "ticket_id": "M008",
        "subject": "Item arrived late - return window expired",
        "body": "My order arrived 3 weeks late, which is past the 30-day return window. The item doesn't fit properly. Can I still return it?",
        "customer_tier": "bronze",
        "priority": "medium",
        "correct_department": "Returns",
        "difficulty": "medium",
        "adjacent_departments": ["Shipping"]
    },
    {
        "ticket_id": "M009",
        "subject": "Recurring charge for cancelled service",
        "body": "I cancelled my subscription 3 months ago but I'm still being charged $15/month. Please stop these charges and refund the last 3 months.",
        "customer_tier": "gold",
        "priority": "high",
        "correct_department": "Billing",
        "difficulty": "medium",
        "adjacent_departments": ["Technical"]
    },
    {
        "ticket_id": "M010",
        "subject": "Feature not working as described",
        "body": "The product description said it includes feature X but mine doesn't have it. Is this a defective unit or was the description wrong?",
        "customer_tier": "silver",
        "priority": "medium",
        "correct_department": "Returns",
        "difficulty": "medium",
        "adjacent_departments": ["Technical"]
    },

    # HARD TICKETS (8) - complex multi-issue tickets requiring reasoning
    {
        "ticket_id": "H001",
        "subject": "Order cancelled but charged, and replacement never sent",
        "body": "I placed order #11111 which was cancelled due to stock issues. However, I was still charged. The support agent said a replacement would be sent automatically but I never received it. It's been 3 weeks.",
        "customer_tier": "platinum",
        "priority": "high",
        "correct_department": "Billing",
        "difficulty": "hard",
        "adjacent_departments": ["Shipping", "Returns", "Technical"]
    },
    {
        "ticket_id": "H002",
        "subject": "System down during upgrade, lost subscription access",
        "body": "During the system upgrade last weekend, my subscription access was lost. Now when I try to renew, the payment system errors out. I've been without service for 5 days and need this resolved urgently.",
        "customer_tier": "gold",
        "priority": "high",
        "correct_department": "Technical",
        "difficulty": "hard",
        "adjacent_departments": ["Billing"]
    },
    {
        "ticket_id": "H003",
        "subject": "Multiple orders mixed up - wrong items, wrong addresses",
        "body": "I placed three orders last week. Order A was sent to the wrong address, Order B contained items from Order C, and Order C never arrived. This is a complete mess. I need all three sorted out.",
        "customer_tier": "platinum",
        "priority": "high",
        "correct_department": "Shipping",
        "difficulty": "hard",
        "adjacent_departments": ["Returns", "Billing", "Technical"]
    },
    {
        "ticket_id": "H004",
        "subject": "Refund processed but never received, account now suspended",
        "body": "I was promised a refund for a defective product. The system shows the refund was processed but I never received it. Now my account is suspended for non-payment of the next billing cycle. This is completely unfair.",
        "customer_tier": "gold",
        "priority": "high",
        "correct_department": "Billing",
        "difficulty": "hard",
        "adjacent_departments": ["Technical", "Returns"]
    },
    {
        "ticket_id": "H005",
        "subject": "Data sync issue causing billing errors across devices",
        "body": "My subscription data isn't syncing between my devices. This caused duplicate charges on my tablet while my phone shows the subscription as expired. The app crashes when I try to sync manually. I need both the billing and sync issues fixed.",
        "customer_tier": "platinum",
        "priority": "high",
        "correct_department": "Technical",
        "difficulty": "hard",
        "adjacent_departments": ["Billing"]
    },
    {
        "ticket_id": "H006",
        "subject": "Return lost in shipping, original payment method expired",
        "body": "I returned an item 2 months ago but the tracking shows it's stuck at a distribution center. The refund can't be processed to my original card because it expired. I need the refund sent to my new payment method and the return situation resolved.",
        "customer_tier": "silver",
        "priority": "medium",
        "correct_department": "Returns",
        "difficulty": "hard",
        "adjacent_departments": ["Shipping", "Billing"]
    },
    {
        "ticket_id": "H007",
        "subject": "Upgrade promotion not applied, overcharged for months",
        "body": "I upgraded my plan using a promotional code that was supposed to give me 50% off for 6 months. The discount was never applied, and I've been paying full price for 4 months. When I try to contact support about this, the ticket system keeps redirecting me in circles.",
        "customer_tier": "gold",
        "priority": "high",
        "correct_department": "Billing",
        "difficulty": "hard",
        "adjacent_departments": ["Technical"]
    },
    {
        "ticket_id": "H008",
        "subject": "Account hacked, fraudulent orders placed, refunds denied",
        "body": "My account was hacked and someone placed 5 fraudulent orders using my saved payment method. I reported this immediately but the orders weren't cancelled in time. Now the refunds are being denied because 'the orders were delivered'. I need these charges reversed and my account secured.",
        "customer_tier": "platinum",
        "priority": "high",
        "correct_department": "Billing",
        "difficulty": "hard",
        "adjacent_departments": ["Technical", "Shipping", "Returns"]
    }
]
