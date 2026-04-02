"""
Apple Product Catalog — All major Apple products from the last 5 years (2021–2026).

Each product has: id, name, category, year, keywords (for matching against
refurbished listings), and an image URL from Apple's public product imagery.
"""

CATEGORIES = [
    {"id": "mac", "name": "Mac", "icon": "💻"},
    {"id": "ipad", "name": "iPad", "icon": "📱"},
    {"id": "iphone", "name": "iPhone", "icon": "📲"},
    {"id": "watch", "name": "Apple Watch", "icon": "⌚"},
    {"id": "airpods", "name": "AirPods", "icon": "🎧"},
    {"id": "appletv", "name": "Apple TV", "icon": "📺"},
    {"id": "homepod", "name": "HomePod", "icon": "🔊"},
    {"id": "accessories", "name": "Accessories", "icon": "🖥️"},
]

PRODUCTS = [
    # =========================================================================
    # MAC — MacBook Air
    # =========================================================================
    {
        "id": "mba-m1-2020",
        "name": "MacBook Air (M1, 2020)",
        "category": "mac",
        "subcategory": "MacBook Air",
        "year": 2020,
        "keywords": ["macbook air", "m1"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/macbook-air-space-gray-select-201810?wid=400&fmt=png-alpha",
    },
    {
        "id": "mba-m2-2022",
        "name": "MacBook Air (M2, 2022)",
        "category": "mac",
        "subcategory": "MacBook Air",
        "year": 2022,
        "keywords": ["macbook air", "m2"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mba-midnight-select-202402?wid=400&fmt=png-alpha",
    },
    {
        "id": "mba-13-m3-2024",
        "name": 'MacBook Air 13" (M3, 2024)',
        "category": "mac",
        "subcategory": "MacBook Air",
        "year": 2024,
        "keywords": ["macbook air", "13", "m3"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mba-midnight-select-202402?wid=400&fmt=png-alpha",
    },
    {
        "id": "mba-15-m3-2024",
        "name": 'MacBook Air 15" (M3, 2024)',
        "category": "mac",
        "subcategory": "MacBook Air",
        "year": 2024,
        "keywords": ["macbook air", "15", "m3"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mba15-midnight-select-202306?wid=400&fmt=png-alpha",
    },
    {
        "id": "mba-13-m4-2025",
        "name": 'MacBook Air 13" (M4, 2025)',
        "category": "mac",
        "subcategory": "MacBook Air",
        "year": 2025,
        "keywords": ["macbook air", "13", "m4"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mba-midnight-select-202402?wid=400&fmt=png-alpha",
    },
    {
        "id": "mba-15-m4-2025",
        "name": 'MacBook Air 15" (M4, 2025)',
        "category": "mac",
        "subcategory": "MacBook Air",
        "year": 2025,
        "keywords": ["macbook air", "15", "m4"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mba15-midnight-select-202306?wid=400&fmt=png-alpha",
    },

    # =========================================================================
    # MAC — MacBook Pro
    # =========================================================================
    {
        "id": "mbp-14-m1pro-2021",
        "name": 'MacBook Pro 14" (M1 Pro/Max, 2021)',
        "category": "mac",
        "subcategory": "MacBook Pro",
        "year": 2021,
        "keywords": ["macbook pro", "14", "m1"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp14-spacegray-select-202110?wid=400&fmt=png-alpha",
    },
    {
        "id": "mbp-16-m1pro-2021",
        "name": 'MacBook Pro 16" (M1 Pro/Max, 2021)',
        "category": "mac",
        "subcategory": "MacBook Pro",
        "year": 2021,
        "keywords": ["macbook pro", "16", "m1"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp16-spacegray-select-202110?wid=400&fmt=png-alpha",
    },
    {
        "id": "mbp-13-m2-2022",
        "name": 'MacBook Pro 13" (M2, 2022)',
        "category": "mac",
        "subcategory": "MacBook Pro",
        "year": 2022,
        "keywords": ["macbook pro", "13", "m2"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp-spacegray-select-202206?wid=400&fmt=png-alpha",
    },
    {
        "id": "mbp-14-m2pro-2023",
        "name": 'MacBook Pro 14" (M2 Pro/Max, 2023)',
        "category": "mac",
        "subcategory": "MacBook Pro",
        "year": 2023,
        "keywords": ["macbook pro", "14", "m2"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp14-spacegray-select-202110?wid=400&fmt=png-alpha",
    },
    {
        "id": "mbp-16-m2pro-2023",
        "name": 'MacBook Pro 16" (M2 Pro/Max, 2023)',
        "category": "mac",
        "subcategory": "MacBook Pro",
        "year": 2023,
        "keywords": ["macbook pro", "16", "m2"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp16-spacegray-select-202110?wid=400&fmt=png-alpha",
    },
    {
        "id": "mbp-14-m3-2023",
        "name": 'MacBook Pro 14" (M3, 2023)',
        "category": "mac",
        "subcategory": "MacBook Pro",
        "year": 2023,
        "keywords": ["macbook pro", "14", "m3"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp14-spacegray-select-202110?wid=400&fmt=png-alpha",
    },
    {
        "id": "mbp-14-m3pro-2023",
        "name": 'MacBook Pro 14" (M3 Pro/Max, 2023)',
        "category": "mac",
        "subcategory": "MacBook Pro",
        "year": 2023,
        "keywords": ["macbook pro", "14", "m3 pro", "m3 max"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp14-spacegray-select-202110?wid=400&fmt=png-alpha",
    },
    {
        "id": "mbp-16-m3pro-2023",
        "name": 'MacBook Pro 16" (M3 Pro/Max, 2023)',
        "category": "mac",
        "subcategory": "MacBook Pro",
        "year": 2023,
        "keywords": ["macbook pro", "16", "m3 pro", "m3 max"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp16-spacegray-select-202110?wid=400&fmt=png-alpha",
    },
    {
        "id": "mbp-14-m4-2024",
        "name": 'MacBook Pro 14" (M4, 2024)',
        "category": "mac",
        "subcategory": "MacBook Pro",
        "year": 2024,
        "keywords": ["macbook pro", "14", "m4"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp14-spacegray-select-202110?wid=400&fmt=png-alpha",
    },
    {
        "id": "mbp-14-m4pro-2024",
        "name": 'MacBook Pro 14" (M4 Pro/Max, 2024)',
        "category": "mac",
        "subcategory": "MacBook Pro",
        "year": 2024,
        "keywords": ["macbook pro", "14", "m4 pro", "m4 max"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp14-spacegray-select-202110?wid=400&fmt=png-alpha",
    },
    {
        "id": "mbp-16-m4pro-2024",
        "name": 'MacBook Pro 16" (M4 Pro/Max, 2024)',
        "category": "mac",
        "subcategory": "MacBook Pro",
        "year": 2024,
        "keywords": ["macbook pro", "16", "m4 pro", "m4 max"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp16-spacegray-select-202110?wid=400&fmt=png-alpha",
    },

    # =========================================================================
    # MAC — iMac
    # =========================================================================
    {
        "id": "imac-m1-2021",
        "name": "iMac 24\" (M1, 2021)",
        "category": "mac",
        "subcategory": "iMac",
        "year": 2021,
        "keywords": ["imac", "24", "m1"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/imac-24-blue-selection-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "imac-m3-2023",
        "name": "iMac 24\" (M3, 2023)",
        "category": "mac",
        "subcategory": "iMac",
        "year": 2023,
        "keywords": ["imac", "24", "m3"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/imac-24-blue-selection-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "imac-m4-2024",
        "name": "iMac 24\" (M4, 2024)",
        "category": "mac",
        "subcategory": "iMac",
        "year": 2024,
        "keywords": ["imac", "24", "m4"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/imac-24-blue-selection-702702?wid=400&fmt=png-alpha",
    },

    # =========================================================================
    # MAC — Mac Mini
    # =========================================================================
    {
        "id": "mac-mini-m1-2020",
        "name": "Mac mini (M1, 2020)",
        "category": "mac",
        "subcategory": "Mac mini",
        "year": 2020,
        "keywords": ["mac mini", "m1"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mac-mini-hero-202011?wid=400&fmt=png-alpha",
    },
    {
        "id": "mac-mini-m2-2023",
        "name": "Mac mini (M2, 2023)",
        "category": "mac",
        "subcategory": "Mac mini",
        "year": 2023,
        "keywords": ["mac mini", "m2"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mac-mini-hero-202011?wid=400&fmt=png-alpha",
    },
    {
        "id": "mac-mini-m2pro-2023",
        "name": "Mac mini (M2 Pro, 2023)",
        "category": "mac",
        "subcategory": "Mac mini",
        "year": 2023,
        "keywords": ["mac mini", "m2 pro"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mac-mini-hero-202011?wid=400&fmt=png-alpha",
    },
    {
        "id": "mac-mini-m4-2024",
        "name": "Mac mini (M4, 2024)",
        "category": "mac",
        "subcategory": "Mac mini",
        "year": 2024,
        "keywords": ["mac mini", "m4"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mac-mini-hero-202011?wid=400&fmt=png-alpha",
    },
    {
        "id": "mac-mini-m4pro-2024",
        "name": "Mac mini (M4 Pro, 2024)",
        "category": "mac",
        "subcategory": "Mac mini",
        "year": 2024,
        "keywords": ["mac mini", "m4 pro"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mac-mini-hero-202011?wid=400&fmt=png-alpha",
    },

    # =========================================================================
    # MAC — Mac Studio
    # =========================================================================
    {
        "id": "mac-studio-m1max-2022",
        "name": "Mac Studio (M1 Max/Ultra, 2022)",
        "category": "mac",
        "subcategory": "Mac Studio",
        "year": 2022,
        "keywords": ["mac studio", "m1"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mac-studio-select-202203?wid=400&fmt=png-alpha",
    },
    {
        "id": "mac-studio-m2max-2023",
        "name": "Mac Studio (M2 Max/Ultra, 2023)",
        "category": "mac",
        "subcategory": "Mac Studio",
        "year": 2023,
        "keywords": ["mac studio", "m2"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mac-studio-select-202203?wid=400&fmt=png-alpha",
    },
    {
        "id": "mac-studio-m4max-2025",
        "name": "Mac Studio (M4 Max/Ultra, 2025)",
        "category": "mac",
        "subcategory": "Mac Studio",
        "year": 2025,
        "keywords": ["mac studio", "m4"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mac-studio-select-202203?wid=400&fmt=png-alpha",
    },

    # =========================================================================
    # MAC — Mac Pro
    # =========================================================================
    {
        "id": "mac-pro-m2ultra-2023",
        "name": "Mac Pro (M2 Ultra, 2023)",
        "category": "mac",
        "subcategory": "Mac Pro",
        "year": 2023,
        "keywords": ["mac pro", "m2 ultra"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mac-pro-tower-select-202306?wid=400&fmt=png-alpha",
    },

    # =========================================================================
    # MAC — Apple Display
    # =========================================================================
    {
        "id": "studio-display-2022",
        "name": "Apple Studio Display (2022)",
        "category": "mac",
        "subcategory": "Display",
        "year": 2022,
        "keywords": ["studio display"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/studio-display-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "pro-display-xdr",
        "name": "Pro Display XDR",
        "category": "mac",
        "subcategory": "Display",
        "year": 2021,
        "keywords": ["pro display xdr"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/pro-display-702702?wid=400&fmt=png-alpha",
    },

    # =========================================================================
    # IPAD
    # =========================================================================
    {
        "id": "ipad-9th-2021",
        "name": "iPad (9th generation, 2021)",
        "category": "ipad",
        "subcategory": "iPad",
        "year": 2021,
        "keywords": ["ipad", "9th"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-2021-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "ipad-10th-2022",
        "name": "iPad (10th generation, 2022)",
        "category": "ipad",
        "subcategory": "iPad",
        "year": 2022,
        "keywords": ["ipad", "10th"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-2022-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "ipad-a16-2024",
        "name": "iPad (A16, 2024)",
        "category": "ipad",
        "subcategory": "iPad",
        "year": 2024,
        "keywords": ["ipad", "a16"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-2022-702702?wid=400&fmt=png-alpha",
    },

    # iPad Mini
    {
        "id": "ipad-mini-6th-2021",
        "name": "iPad mini (6th generation, 2021)",
        "category": "ipad",
        "subcategory": "iPad mini",
        "year": 2021,
        "keywords": ["ipad mini", "6th"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-mini-select-202109?wid=400&fmt=png-alpha",
    },
    {
        "id": "ipad-mini-a17pro-2024",
        "name": "iPad mini (A17 Pro, 2024)",
        "category": "ipad",
        "subcategory": "iPad mini",
        "year": 2024,
        "keywords": ["ipad mini", "a17"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-mini-select-202109?wid=400&fmt=png-alpha",
    },

    # iPad Air
    {
        "id": "ipad-air-m1-2022",
        "name": "iPad Air (M1, 2022)",
        "category": "ipad",
        "subcategory": "iPad Air",
        "year": 2022,
        "keywords": ["ipad air", "m1"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-air-select-202203?wid=400&fmt=png-alpha",
    },
    {
        "id": "ipad-air-11-m2-2024",
        "name": 'iPad Air 11" (M2, 2024)',
        "category": "ipad",
        "subcategory": "iPad Air",
        "year": 2024,
        "keywords": ["ipad air", "11", "m2"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-air-select-202203?wid=400&fmt=png-alpha",
    },
    {
        "id": "ipad-air-13-m2-2024",
        "name": 'iPad Air 13" (M2, 2024)',
        "category": "ipad",
        "subcategory": "iPad Air",
        "year": 2024,
        "keywords": ["ipad air", "13", "m2"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-air-select-202203?wid=400&fmt=png-alpha",
    },
    {
        "id": "ipad-air-11-m3-2025",
        "name": 'iPad Air 11" (M3, 2025)',
        "category": "ipad",
        "subcategory": "iPad Air",
        "year": 2025,
        "keywords": ["ipad air", "11", "m3"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-air-select-202203?wid=400&fmt=png-alpha",
    },
    {
        "id": "ipad-air-13-m3-2025",
        "name": 'iPad Air 13" (M3, 2025)',
        "category": "ipad",
        "subcategory": "iPad Air",
        "year": 2025,
        "keywords": ["ipad air", "13", "m3"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-air-select-202203?wid=400&fmt=png-alpha",
    },

    # iPad Pro
    {
        "id": "ipad-pro-11-m1-2021",
        "name": 'iPad Pro 11" (M1, 2021)',
        "category": "ipad",
        "subcategory": "iPad Pro",
        "year": 2021,
        "keywords": ["ipad pro", "11", "m1"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-pro-11-select-202104?wid=400&fmt=png-alpha",
    },
    {
        "id": "ipad-pro-129-m1-2021",
        "name": 'iPad Pro 12.9" (M1, 2021)',
        "category": "ipad",
        "subcategory": "iPad Pro",
        "year": 2021,
        "keywords": ["ipad pro", "12.9", "m1"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-pro-12-select-202104?wid=400&fmt=png-alpha",
    },
    {
        "id": "ipad-pro-11-m2-2022",
        "name": 'iPad Pro 11" (M2, 2022)',
        "category": "ipad",
        "subcategory": "iPad Pro",
        "year": 2022,
        "keywords": ["ipad pro", "11", "m2"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-pro-11-select-202104?wid=400&fmt=png-alpha",
    },
    {
        "id": "ipad-pro-129-m2-2022",
        "name": 'iPad Pro 12.9" (M2, 2022)',
        "category": "ipad",
        "subcategory": "iPad Pro",
        "year": 2022,
        "keywords": ["ipad pro", "12.9", "m2"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-pro-12-select-202104?wid=400&fmt=png-alpha",
    },
    {
        "id": "ipad-pro-11-m4-2024",
        "name": 'iPad Pro 11" (M4, 2024)',
        "category": "ipad",
        "subcategory": "iPad Pro",
        "year": 2024,
        "keywords": ["ipad pro", "11", "m4"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-pro-11-select-202104?wid=400&fmt=png-alpha",
    },
    {
        "id": "ipad-pro-13-m4-2024",
        "name": 'iPad Pro 13" (M4, 2024)',
        "category": "ipad",
        "subcategory": "iPad Pro",
        "year": 2024,
        "keywords": ["ipad pro", "13", "m4"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/ipad-pro-12-select-202104?wid=400&fmt=png-alpha",
    },

    # =========================================================================
    # IPHONE
    # =========================================================================
    {
        "id": "iphone-13-2021",
        "name": "iPhone 13",
        "category": "iphone",
        "subcategory": "iPhone",
        "year": 2021,
        "keywords": ["iphone 13"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-13-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-13-mini-2021",
        "name": "iPhone 13 mini",
        "category": "iphone",
        "subcategory": "iPhone",
        "year": 2021,
        "keywords": ["iphone 13 mini"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-13-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-13-pro-2021",
        "name": "iPhone 13 Pro",
        "category": "iphone",
        "subcategory": "iPhone Pro",
        "year": 2021,
        "keywords": ["iphone 13 pro"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-13-pro-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-13-pro-max-2021",
        "name": "iPhone 13 Pro Max",
        "category": "iphone",
        "subcategory": "iPhone Pro",
        "year": 2021,
        "keywords": ["iphone 13 pro max"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-13-pro-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-14-2022",
        "name": "iPhone 14",
        "category": "iphone",
        "subcategory": "iPhone",
        "year": 2022,
        "keywords": ["iphone 14"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-14-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-14-plus-2022",
        "name": "iPhone 14 Plus",
        "category": "iphone",
        "subcategory": "iPhone",
        "year": 2022,
        "keywords": ["iphone 14 plus"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-14-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-14-pro-2022",
        "name": "iPhone 14 Pro",
        "category": "iphone",
        "subcategory": "iPhone Pro",
        "year": 2022,
        "keywords": ["iphone 14 pro"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-14-pro-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-14-pro-max-2022",
        "name": "iPhone 14 Pro Max",
        "category": "iphone",
        "subcategory": "iPhone Pro",
        "year": 2022,
        "keywords": ["iphone 14 pro max"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-14-pro-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-15-2023",
        "name": "iPhone 15",
        "category": "iphone",
        "subcategory": "iPhone",
        "year": 2023,
        "keywords": ["iphone 15"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-15-plus-2023",
        "name": "iPhone 15 Plus",
        "category": "iphone",
        "subcategory": "iPhone",
        "year": 2023,
        "keywords": ["iphone 15 plus"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-15-pro-2023",
        "name": "iPhone 15 Pro",
        "category": "iphone",
        "subcategory": "iPhone Pro",
        "year": 2023,
        "keywords": ["iphone 15 pro"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-15-pro-max-2023",
        "name": "iPhone 15 Pro Max",
        "category": "iphone",
        "subcategory": "iPhone Pro",
        "year": 2023,
        "keywords": ["iphone 15 pro max"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-16-2024",
        "name": "iPhone 16",
        "category": "iphone",
        "subcategory": "iPhone",
        "year": 2024,
        "keywords": ["iphone 16"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-16-plus-2024",
        "name": "iPhone 16 Plus",
        "category": "iphone",
        "subcategory": "iPhone",
        "year": 2024,
        "keywords": ["iphone 16 plus"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-16-pro-2024",
        "name": "iPhone 16 Pro",
        "category": "iphone",
        "subcategory": "iPhone Pro",
        "year": 2024,
        "keywords": ["iphone 16 pro"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-16-pro-max-2024",
        "name": "iPhone 16 Pro Max",
        "category": "iphone",
        "subcategory": "iPhone Pro",
        "year": 2024,
        "keywords": ["iphone 16 pro max"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "iphone-16e-2025",
        "name": "iPhone 16e",
        "category": "iphone",
        "subcategory": "iPhone",
        "year": 2025,
        "keywords": ["iphone 16e", "iphone se"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-702702?wid=400&fmt=png-alpha",
    },

    # =========================================================================
    # APPLE WATCH
    # =========================================================================
    {
        "id": "watch-series-7-2021",
        "name": "Apple Watch Series 7 (2021)",
        "category": "watch",
        "subcategory": "Apple Watch",
        "year": 2021,
        "keywords": ["apple watch", "series 7"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/apple-watch-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "watch-series-8-2022",
        "name": "Apple Watch Series 8 (2022)",
        "category": "watch",
        "subcategory": "Apple Watch",
        "year": 2022,
        "keywords": ["apple watch", "series 8"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/apple-watch-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "watch-se-2022",
        "name": "Apple Watch SE (2nd gen, 2022)",
        "category": "watch",
        "subcategory": "Apple Watch SE",
        "year": 2022,
        "keywords": ["apple watch", "se"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/apple-watch-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "watch-ultra-2022",
        "name": "Apple Watch Ultra (2022)",
        "category": "watch",
        "subcategory": "Apple Watch Ultra",
        "year": 2022,
        "keywords": ["apple watch", "ultra"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/apple-watch-ultra-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "watch-series-9-2023",
        "name": "Apple Watch Series 9 (2023)",
        "category": "watch",
        "subcategory": "Apple Watch",
        "year": 2023,
        "keywords": ["apple watch", "series 9"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/apple-watch-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "watch-ultra-2-2023",
        "name": "Apple Watch Ultra 2 (2023)",
        "category": "watch",
        "subcategory": "Apple Watch Ultra",
        "year": 2023,
        "keywords": ["apple watch", "ultra 2"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/apple-watch-ultra-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "watch-series-10-2024",
        "name": "Apple Watch Series 10 (2024)",
        "category": "watch",
        "subcategory": "Apple Watch",
        "year": 2024,
        "keywords": ["apple watch", "series 10"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/apple-watch-702702?wid=400&fmt=png-alpha",
    },

    # =========================================================================
    # AIRPODS
    # =========================================================================
    {
        "id": "airpods-3rd-2021",
        "name": "AirPods (3rd generation, 2021)",
        "category": "airpods",
        "subcategory": "AirPods",
        "year": 2021,
        "keywords": ["airpods", "3rd"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/airpods-3rd-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "airpods-4-2024",
        "name": "AirPods 4 (2024)",
        "category": "airpods",
        "subcategory": "AirPods",
        "year": 2024,
        "keywords": ["airpods 4", "airpods"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/airpods-3rd-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "airpods-4-anc-2024",
        "name": "AirPods 4 with ANC (2024)",
        "category": "airpods",
        "subcategory": "AirPods",
        "year": 2024,
        "keywords": ["airpods 4", "noise cancel"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/airpods-3rd-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "airpods-pro-2nd-2022",
        "name": "AirPods Pro (2nd generation, 2022)",
        "category": "airpods",
        "subcategory": "AirPods Pro",
        "year": 2022,
        "keywords": ["airpods pro", "2nd"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/airpods-pro-2nd-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "airpods-max-2020",
        "name": "AirPods Max (2020)",
        "category": "airpods",
        "subcategory": "AirPods Max",
        "year": 2020,
        "keywords": ["airpods max"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/airpods-max-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "airpods-max-usbc-2024",
        "name": "AirPods Max USB-C (2024)",
        "category": "airpods",
        "subcategory": "AirPods Max",
        "year": 2024,
        "keywords": ["airpods max", "usb-c"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/airpods-max-702702?wid=400&fmt=png-alpha",
    },

    # =========================================================================
    # APPLE TV
    # =========================================================================
    {
        "id": "appletv-4k-2021",
        "name": "Apple TV 4K (2nd generation, 2021)",
        "category": "appletv",
        "subcategory": "Apple TV",
        "year": 2021,
        "keywords": ["apple tv", "4k"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/apple-tv-4k-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "appletv-4k-2022",
        "name": "Apple TV 4K (3rd generation, 2022)",
        "category": "appletv",
        "subcategory": "Apple TV",
        "year": 2022,
        "keywords": ["apple tv", "4k", "3rd"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/apple-tv-4k-702702?wid=400&fmt=png-alpha",
    },

    # =========================================================================
    # HOMEPOD
    # =========================================================================
    {
        "id": "homepod-2nd-2023",
        "name": "HomePod (2nd generation, 2023)",
        "category": "homepod",
        "subcategory": "HomePod",
        "year": 2023,
        "keywords": ["homepod"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/homepod-702702?wid=400&fmt=png-alpha",
    },
    {
        "id": "homepod-mini",
        "name": "HomePod mini",
        "category": "homepod",
        "subcategory": "HomePod mini",
        "year": 2021,
        "keywords": ["homepod mini"],
        "image": "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/homepod-mini-702702?wid=400&fmt=png-alpha",
    },
]


def get_all_products():
    return PRODUCTS


def get_categories():
    return CATEGORIES


def get_products_by_category(category_id):
    return [p for p in PRODUCTS if p["category"] == category_id]


def get_product_by_id(product_id):
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return None
