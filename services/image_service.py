import os

class DishImageService:
    def __init__(self):
        self.dish_images = {
            # 🍲 SOUPS AND STEWS
            
            ### Egusi Soups
            "Egusi Soup with Beef": "/images/egusi.jpg",
            "Egusi Soup with Fish": "/images/egusi.jpg", 
            "Egusi Soup with Assorted Meat": "/images/egusi.jpg",
            "Egusi Soup with Goat Meat": "/images/egusi.jpg",

            ### Ogbono Soups
            "Ogbono Soup with Beef": "/images/ogbono.jpeg",
            "Ogbono Soup with Fish": "/images/ogbono.jpeg",
            "Ogbono Soup with Okporoko (Stockfish)": "/images/ogbono.jpeg",

            ### Vegetable Soups
            "Vegetable Soup (Efo Riro)": "/images/vegetable-soup.png",
            "Bitterleaf Soup (Ofe Onugbu)": "/images/bitterleaf-soup.jpeg",
            "Oha Soup": "/images/oha-soup.jpg",
            "Afang Soup": "/images/afang.jpg",
            "Edikaikong Soup": "/images/edikaikong.jpg",

            ### Other Soups
            "White Soup (Ofe Nsala)": "/images/white-soup.jpg",
            "Banga Soup": "/images/banga.jpg",
            "Pepper Soup (Goat)": "/images/pepper-soup-goat.jpg",
            "Pepper Soup (Fish)": "/images/pepper-soup-fish.jpg",

            # 🍚 SWALLOWS (STARCHY FOODS)
            "Pounded Yam": "/images/pounded-yam.jpg",
            "Fufu": "/images/fufu.jpg",
            "Eba": "/images/eba.jpg",
            "Amala": "/images/amala.jpg",
            "Semovita": "/images/semo.jpg",
            "Wheat": "/images/wheat-swallow.jpg",

            # 🍚 RICE DISHES
            
            ### Jollof Rice
            "Plain Jollof Rice": "/images/jollof-protein.jpeg",
            "Jollof Rice with Chicken": "/images/jollof-protein.jpeg",
            "Jollof Rice with Beef": "/images/jollof-protein.jpeg",
            "Party Jollof Rice": "/images/jollof-protein.jpeg",

            ### Other Rice Dishes
            "Fried Rice with Chicken": "/images/fried-rice.jpg",
            "Fried Rice with Beef": "/images/fried-rice.jpg",
            "Coconut Rice": "/images/coconut-rice.jpg",
            "Ofada Rice with Ayamase Sauce": "/images/ofada-rice.jpg",
            "White Rice and Stew": "/images/white-rice-stew.jpg",

            # 🍗 PROTEIN AND MEAT DISHES
            
            ### Chicken
            "Grilled Chicken (1/4)": "/images/chicken.jpg",
            "Grilled Chicken (1/2)": "/images/chicken.jpg",
            "Fried Chicken (1/4)": "/images/chicken.jpg",
            "Chicken Stew": "/images/chicken.jpg",

            ### Beef and Goat
            "Beef Stew": "/images/assorted-meat.jpg",
            "Grilled Beef (Suya Style)": "/images/suya.jpg",
            "Goat Meat Pepper Soup": "/images/pepper-soup-goat.jpg",
            "Nkwobi (Spicy Cow Foot)": "/images/nkwobi.jpg",

            ### Fish and Seafood
            "Grilled Tilapia": "/images/tilapia.jpg",
            "Grilled Catfish (Point & Kill)": "/images/catfish.jpg",
            "Fried Fish": "/images/fried-fish.jpg",
            "Fish Stew": "/images/fish-stew.jpg",

            # 🍢 SNACKS AND STREET FOOD
            
            ### Suya and Barbecue
            "Beef Suya": "/images/suya.jpg",
            "Chicken Suya": "/images/chicken-suya.jpg",
            "Ram Suya": "/images/ram-suya.jpg",
            "Kilishi (Dried Suya)": "/images/kilishi.jpg",

            ### Small Chops
            "Samosa (2 pieces)": "/images/samosa.jpg",
            "Spring Rolls (3 pieces)": "/images/spring-rolls.jpg",
            "Puff Puff (5 pieces)": "/images/puff-puff.jpg",
            "Meat Pie": "/images/meat-pie.jpg",
            "Scotch Egg": "/images/scotch-egg.jpg",

            ### Traditional Snacks
            "Akara (Bean Cake)": "/images/akara.jpg",
            "Moi Moi": "/images/moi-moi.jpg",
            "Roasted Plantain (Bole)": "/images/boli.jpg",
            "Fried Plantain (Dodo)": "/images/dodo.jpg",

            # 🥗 SIDES AND EXTRAS
            "Fried Plantain": "/images/dodo.jpg",
            "Boiled Plantain": "/images/boiled-plantain.jpg",
            "Boiled Yam": "/images/boiled-yam.jpg",
            "Fried Yam": "/images/fried-yam.jpg",
            "Garden Salad": "/images/garden-salad.jpg",
            "Moin Moin": "/images/moi-moi.jpg",
            "Egg (Fried or Boiled)": "/images/egg.jpg",

            # 🥤 DRINKS AND BEVERAGES
            
            ### Nigerian Traditional Drinks
            "Zobo Drink": "/images/zobo.jpg",
            "Kunu Aya (Tiger Nut Drink)": "/images/kunu-aya.jpg",
            "Fura da Nono": "/images/fura-da-nono.jpg",
            "Chapman": "/images/chapman.jpg",

            ### Fruit Juices
            "Orange Juice": "/images/orange-juice.jpg",
            "Pineapple Juice": "/images/pineapple-juice.jpg",
            "Mango Juice": "/images/mango-juice.jpg",
            "Chapman Special": "/images/chapman-special.jpg",

            ### Soft Drinks and Water
            "Coke (35cl)": "/images/coke.jpeg",
            "Fanta (35cl)": "/images/fanta.jpg",
            "Sprite (35cl)": "/images/sprite.jpg",
            "Maltina": "/images/maltina.jpg",
            "Bottled Water (50cl)": "/images/water.jpg",

            ### Hot Beverages
            "Tea": "/images/tea.jpg",
            "Coffee": "/images/coffee.jpg",
            "Milo": "/images/milo.jpg",
            "Hot Chocolate": "/images/hot-chocolate.jpg",

            # 🍰 DESSERTS AND SWEETS
            "Chin Chin": "/images/chin-chin.jpg",
            "Puff Puff with Sugar": "/images/puff-puff.jpg",
            "Coconut Candy": "/images/coconut-candy.jpg",
            "Ice Cream (Scoop)": "/images/ice-cream.jpg",
            "Fruit Salad": "/images/fruit-salad.jpg",

            # 🍛 COMBO MEALS
            
            ### Executive Combos
            "Jollof Rice + Chicken + Salad + Drink": "/images/jollof-protein.jpeg",
            "Fried Rice + Beef + Plantain + Drink": "/images/fried-rice.jpg",
            "Pounded Yam + Egusi Soup + Assorted Meat": "/images/pounded-yam.jpg",

            ### Student Combos
            "Jollof Rice + Chicken": "/images/jollof-protein.jpeg",
            "Fried Rice + Beef": "/images/fried-rice.jpg",

            ### Family Packs
            "Family Jollof Rice Pack (Serves 4)": "/images/jollof-protein.jpeg",
            "Family Fried Rice Pack (Serves 4)": "/images/fried-rice.jpg",

            # 🎉 PARTY PACKS
            "Small Party Pack (Serves 10)": "/images/party-pack.jpg",
            "Medium Party Pack (Serves 20)": "/images/party-pack.jpg",
            "Large Party Pack (Serves 50)": "/images/party-pack.jpg"
        }
    
    def get_dish_image(self, dish_name):
        """Get image URL for a dish"""
        # First try exact match
        if dish_name in self.dish_images:
            return self.dish_images[dish_name]
        
        # Then try partial match
        for key in self.dish_images:
            if key.lower() in dish_name.lower():
                return self.dish_images[key]
        
        # If no match found, return None
        return None
    def get_images_for_order(self, order_text):
        """Extract dish images from order text"""
        images = []
        order_lower = order_text.lower()
        
        # Check each dish name against the order text
        for dish_name, image_url in self.dish_images.items():
            # Convert dish name to searchable format (remove special characters, prices, etc.)
            search_name = dish_name.split(' - ')[0].split(' (')[0].lower()
            
            if search_name in order_lower:
                if image_url not in images:  # Avoid duplicates
                    images.append(image_url)
        
        return images[:4]  # Max 4 images to avoid clutter
    
    def get_all_dishes_by_category(self):
        """Return dishes organized by category for debugging"""
        categories = {
            "Egusi Soups": [],
            "Ogbono Soups": [],
            "Vegetable Soups": [],
            "Other Soups": [],
            "Swallows": [],
            "Jollof Rice": [],
            "Other Rice Dishes": [],
            "Chicken": [],
            "Beef and Goat": [],
            "Fish and Seafood": [],
            "Suya and Barbecue": [],
            "Small Chops": [],
            "Traditional Snacks": [],
            "Sides and Extras": [],
            "Nigerian Traditional Drinks": [],
            "Fruit Juices": [],
            "Soft Drinks and Water": [],
            "Hot Beverages": [],
            "Desserts and Sweets": [],
            "Executive Combos": [],
            "Student Combos": [],
            "Family Packs": [],
            "Party Packs": []
        }
        
        # This is a helper method to see which dishes have images
        for dish_name, image_url in self.dish_images.items():
            # To map dishes to categories - this is simplified
            print(f"'{dish_name}': '{image_url}',")
        
        return categories