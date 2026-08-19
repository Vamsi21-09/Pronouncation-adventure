"""World 1: Sunlit Village (Levels 1 to 30, 210 unique words)."""
from __future__ import annotations

# Format: (text, meaning, sentence, hint, syllables, mistake, alt)
WORLD_1_LEVELS = [
    # L1: 2-letter basic sight/sound words
    [
        ("am", "Used to say who you are or how you feel.", "I am happy to learn new words today.", "AM", "am", "Dropping the 'm' nasal sound at the end.", "A cheerful child pointing to themselves"),
        ("at", "Used to show a place or time.", "We will meet at the village garden gate.", "AT", "at", "Saying 'et' instead of the short 'a' sound.", "A wooden gate in front of a garden path"),
        ("in", "Inside of a container, room, or area.", "The cozy cat is resting in the basket.", "IN", "in", "Confusing short 'i' with 'ee'.", "A fluffy kitten sitting inside a wicker basket"),
        ("on", "Supported by or touching a surface.", "The warm teapot rests on the wooden table.", "ON", "on", "Saying 'un' instead of open 'o'.", "A ceramic teapot resting on top of a table"),
        ("up", "Moving toward a higher place.", "The colorful kite flew high up into the air.", "UP", "up", "Saying 'op' instead of short 'u'.", "A brightly colored kite soaring upward into the sky"),
        ("to", "Moving in the direction of a place.", "We are walking to the village library.", "TOO", "to", "Over-pronouncing as 'toe'.", "A cobblestone path leading to a village building"),
        ("go", "To move from one place to another.", "The children go to the playground after lunch.", "GOH", "go", "Saying 'goo' instead of long 'o'.", "Happy children walking toward a park playground"),
    ],
    # L2: 3-letter simple CVC words (animals & nature)
    [
        ("cat", "A small furry animal often kept as a pet.", "The playful cat chased the yarn ball.", "KAT", "cat", "Saying 'ket' instead of short 'a'.", "A friendly calico cat with whiskers"),
        ("dog", "A loyal four-legged animal that barks.", "The happy dog wagged its tail at the door.", "DAWG", "dog", "Saying 'duk' or dropping the voiced 'g'.", "A golden retriever sitting happily on the grass"),
        ("sun", "The bright star that lights our daytime sky.", "The morning sun warmed the village square.", "SUN", "sun", "Saying 'son' with a long vowel.", "A shining yellow sun radiating warm light"),
        ("run", "To move quickly on your feet.", "The children run across the open green field.", "RUN", "run", "Confusing 'r' and 'w' sound.", "Two children running happily through a sunny field"),
        ("bat", "A flying mammal that comes out at twilight.", "A gentle brown bat flew over the village trees.", "BAT", "bat", "Saying 'bet' instead of short 'a'.", "A small brown bat flying gracefully in twilight"),
        ("fox", "A clever wild animal with a bushy tail.", "A red fox stepped quietly near the fence.", "FAHKS", "fox", "Saying 'foks' with a hard 'k' only.", "A clever red fox with a bushy tail in the grass"),
        ("pig", "A farm animal with a curly tail and snout.", "The cheerful pink pig splashed near the barn.", "PIG", "pig", "Pronouncing as 'peek' with long 'e'.", "A clean pink piglet smiling near a wooden fence"),
    ],
    # L3: 3-letter household & daily objects
    [
        ("cup", "A small container used for drinking tea or milk.", "She drank warm cocoa from her favorite cup.", "KUHP", "cup", "Saying 'cop' instead of short 'u'.", "A ceramic cup filled with hot cocoa"),
        ("bed", "A comfortable piece of furniture for sleeping.", "He tucked himself into bed under a warm quilt.", "BED", "bed", "Saying 'bad' instead of short 'e'.", "A cozy wooden bed with pillows and blankets"),
        ("hat", "Clothing worn on top of the head for protection.", "She wore a straw hat to block the bright sunlight.", "HAT", "hat", "Saying 'hut' instead of short 'a'.", "A woven straw sun hat with a blue ribbon"),
        ("nut", "A hard-shelled dry fruit with an edible seed.", "The squirrel hid an acorn nut under the leaves.", "NUHT", "nut", "Saying 'not' instead of short 'u'.", "A shiny brown hazelnut resting on a leaf"),
        ("map", "A drawing showing roads, rivers, and cities.", "The explorer opened a colorful map of the realm.", "MAP", "map", "Saying 'mop' instead of short 'a'.", "A rolled parchment map showing village roads and trails"),
        ("pin", "A tiny thin piece of metal used to fasten cloth.", "The tailor used a small pin to hold the ribbon.", "PIN", "pin", "Confusing 'pin' with 'pen'.", "A small shiny metal safety pin"),
        ("bus", "A large vehicle carrying many passengers.", "The yellow village bus arrived at the stop on time.", "BUHS", "bus", "Saying 'boss' instead of short 'u'.", "A cheerful yellow school bus on a country road"),
    ],
    # L4: 3-letter tools, animals, and items
    [
        ("pen", "A tool with ink used for writing or drawing.", "The teacher wrote a note using a blue ink pen.", "PEN", "pen", "Saying 'pin' instead of short 'e'.", "A fountain pen with blue ink resting on parchment"),
        ("top", "The highest part of an object or a spinning toy.", "The wooden toy spun quickly on top of the table.", "TAHP", "top", "Saying 'tap' instead of short 'o'.", "A colorful wooden spinning top toy on a wooden floor"),
        ("box", "A container with stiff sides and a lid.", "She stored her colored markers inside the box.", "BAHKS", "box", "Dropping the final 'ks' sound.", "A neatly wrapped cardboard storage box"),
        ("hen", "A female chicken that lays fresh eggs.", "The brown hen pecked grains in the coop yard.", "HEN", "hen", "Saying 'han' instead of short 'e'.", "A speckled brown hen standing in a farm coop"),
        ("cow", "A large farm animal that provides fresh milk.", "The gentle spotted cow grazed on the hillside.", "KOW", "cow", "Saying 'coo' instead of dipthong 'ow'.", "A black and white spotted dairy cow in a pasture"),
        ("log", "A thick piece of cut wood from a tree trunk.", "We sat together on a sturdy cedar log by the path.", "LAWG", "log", "Saying 'lug' instead of short 'o'.", "A sturdy wooden tree log lying beside a nature path"),
        ("cap", "A small tight-fitting hat with a curved visor.", "He put on his baseball cap before going outside.", "KAP", "cap", "Saying 'cup' instead of short 'a'.", "A red fabric cap with a curved front brim"),
    ],
    # L5: 3-letter rhyming & action words
    [
        ("can", "A sealed metal container for keeping food fresh.", "She opened a can of sweet yellow corn.", "KAN", "can", "Saying 'ken' instead of short 'a'.", "A clean tin can with a label on a kitchen counter"),
        ("fan", "A device that creates a cool breeze of air.", "The electric fan kept the room cool in summer.", "FAN", "fan", "Saying 'fen' instead of short 'a'.", "A small oscillating table fan blowing cool air"),
        ("jam", "A sweet spread made by boiling fruit with sugar.", "He spread delicious strawberry jam on warm toast.", "JAM", "jam", "Saying 'gem' instead of short 'a'.", "A glass jar of red strawberry jam with a spoon"),
        ("pan", "A flat metal container used for cooking food.", "The chef fried golden eggs in the skillet pan.", "PAN", "pan", "Saying 'pin' instead of short 'a'.", "A stainless steel cooking frying pan on a stove"),
        ("tag", "A small label attached to an item to show info.", "The new luggage bag had a name tag tied to it.", "TAG", "tag", "Saying 'teg' instead of short 'a'.", "A paper gift tag with a string ribbon"),
        ("bag", "A flexible container used for carrying things.", "She carried fresh apples in her canvas tote bag.", "BAG", "bag", "Dropping the voiced 'g' ending.", "A cloth tote bag filled with fresh groceries"),
        ("zip", "To fasten or close with a slide fastener.", "Remember to zip your warm jacket against the cold.", "ZIP", "zip", "Saying 'sip' instead of voiced 'z'.", "A metal zipper being pulled up on a blue jacket"),
    ],
    # L6: 4-letter short words (nature, home, food)
    [
        ("bell", "A hollow metal cup that rings with sound.", "The town clock rang its golden bell at noon.", "BEL", "bell", "Dropping the final 'l' liquid sound.", "A polished brass bell hanging in a steeple tower"),
        ("milk", "A white nutrient-rich liquid from cows or goats.", "He poured a glass of cold fresh milk for breakfast.", "MILK", "milk", "Saying 'melk' instead of short 'i'.", "A clear glass filled with fresh cold white milk"),
        ("nest", "A structure built by birds to hold eggs and chicks.", "The robin wove twigs to build a safe nest in the tree.", "NEST", "nest", "Dropping the 'st' final blend.", "A cozy bird nest with three speckled blue eggs"),
        ("star", "A luminous point of light in the night sky.", "The bright evening star twinkled over the rooftops.", "STAHR", "star", "Saying 'stare' instead of 'ar' sound.", "A glowing five-pointed star shining brightly at night"),
        ("fish", "A creature with fins and gills that swims in water.", "A silver fish swam quickly through the clear pond.", "FISH", "fish", "Saying 'feesh' with long 'e'.", "A colorful goldfish swimming in clean river water"),
        ("ship", "A large seafaring vessel that sails across oceans.", "The tall wooden ship docked safely at the harbor.", "SHIP", "ship", "Saying 'sheep' with long 'e'.", "A majestic sailing ship with white sails on the water"),
        ("book", "A set of printed pages bound together with stories.", "She read an exciting adventure book before bedtime.", "BUK", "book", "Saying 'buke' with long 'oo'.", "An open hardcover storybook with colorful illustrations"),
    ],
    # L7: 4-letter simple objects & sounds
    [
        ("door", "A hinged panel used to enter or exit a room.", "She opened the front door to welcome her guests.", "DOR", "door", "Saying 'dour' or 'dar'.", "A welcoming wooden front door with a brass doorknob"),
        ("lamp", "A device that provides electric or flame light.", "The bedside lamp cast a gentle glow across the desk.", "LAMP", "lamp", "Dropping the final 'mp' blend.", "A glowing table lamp on a wooden nightstand"),
        ("desk", "A table with drawers used for writing or studying.", "He organized his notebooks neatly on the study desk.", "DESK", "desk", "Saying 'daks' or dropping 'k'.", "A tidy wooden student desk with a pencil holder"),
        ("frog", "An amphibian with strong legs for hopping.", "A bright green frog jumped from the lily pad.", "FRAWG", "frog", "Saying 'frug' instead of short 'o'.", "A cheerful green tree frog sitting on a green lily pad"),
        ("duck", "A water bird with webbed feet and a flat beak.", "The yellow duck quacked as it swam near the reeds.", "DUHK", "duck", "Saying 'dock' instead of short 'u'.", "A cute yellow duck paddling in clean pond water"),
        ("drum", "A musical instrument played by beating with sticks.", "He tapped a steady rhythm on the wooden drum.", "DRUHM", "drum", "Confusing 'dr' blend with 'jr'.", "A wooden snare drum with two wooden drumsticks"),
        ("flag", "A piece of cloth with distinctive colors and symbols.", "The village flag waved proudly in the morning breeze.", "FLAG", "flag", "Dropping the voiced 'g' ending.", "A colorful banner flag fluttering on a tall flagpole"),
    ],
    # L8: 4-letter landscape & village features
    [
        ("park", "A public area of land with grass and trees.", "The family enjoyed a picnic lunch in the sunny park.", "PAHRK", "park", "Saying 'pork' instead of 'ar'.", "A scenic public park with lush green lawns and benches"),
        ("yard", "An area of ground surrounding a home or building.", "Flowers bloomed brightly across the sunny front yard.", "YAHRD", "yard", "Dropping the 'r' coloring.", "A tidy grassy yard enclosed by a low wooden picket fence"),
        ("barn", "A large farm building used for storing hay and animals.", "The red barn sheltered the horses during the rain.", "BAHRN", "barn", "Saying 'born' instead of 'ar'.", "A classic red wooden farm barn with white trim"),
        ("farm", "An area of land dedicated to growing crops and animals.", "The family grew corn and wheat on their country farm.", "FAHRM", "farm", "Dropping the final 'm' sound.", "A scenic countryside farm with green rolling crop fields"),
        ("gate", "A hinged barrier used to close an opening in a fence.", "He unlatched the garden gate to walk along the trail.", "GAYT", "gate", "Saying 'get' instead of long 'a'.", "A decorative wrought iron garden gate swinging open"),
        ("hill", "A naturally raised area of land smaller than a mountain.", "The children rolled down the grassy green hill.", "HIL", "hill", "Saying 'heel' with long 'e'.", "A gentle grassy hill with wildflowers under a blue sky"),
        ("pond", "A small body of still water surrounded by land.", "Water lilies floated peacefully on the surface of the pond.", "PAHND", "pond", "Saying 'pound' or 'pund'.", "A tranquil village pond surrounded by green weeping willows"),
    ],
    # L9: 4-letter weather & pathways
    [
        ("rock", "A solid mass of natural stone found in nature.", "A smooth round rock rested near the stream bank.", "RAHK", "rock", "Saying 'rook' with long 'oo'.", "A smooth gray river rock resting beside running water"),
        ("sand", "Loose granular particles found on beaches and dunes.", "The children built castles in the soft golden sand.", "SAND", "sand", "Saying 'send' instead of short 'a'.", "Fine golden beach sand with gentle wind ripples"),
        ("wind", "A natural moving current of air outdoors.", "A gentle autumn wind rustled the golden leaves.", "WIND", "wind", "Saying 'wynd' with long 'i'.", "Wind blowing autumn leaves swirling across the air"),
        ("rain", "Water falling in drops from clouds in the sky.", "Gentle rain helped the vegetables grow in the garden.", "RAYN", "rain", "Saying 'ren' with short 'e'.", "Fresh raindrops falling onto green garden leaves"),
        ("snow", "Soft white frozen water crystals falling as flakes.", "Fresh white snow covered the rooftops overnight.", "SNOH", "snow", "Saying 'snout' instead of long 'o'.", "Glistening white snowflakes falling gently on village roofs"),
        ("road", "A paved or cleared pathway for traveling.", "The winding country road led directly to the village.", "ROHD", "road", "Saying 'rod' with short 'o'.", "A paved two-lane country road stretching through hills"),
        ("path", "A narrow track made for walking on foot.", "We followed the scenic stone path through the trees.", "PATH", "path", "Saying 'pet' or mispronouncing unvoiced 'th'.", "A winding cobblestone walking path through flowerbeds"),
    ],
    # L10: 4-letter village tools & buildings
    [
        ("shop", "A building or room where goods and services are sold.", "She bought fresh bakery bread at the corner shop.", "SHAHP", "shop", "Saying 'chop' instead of 'sh' sound.", "A quaint village storefront with glass display windows"),
        ("cart", "A strong vehicle with wheels pulled to carry loads.", "The farmer loaded ripe pumpkins into the wooden cart.", "KAHRT", "cart", "Saying 'court' instead of 'ar'.", "A traditional two-wheeled wooden cart filled with harvest"),
        ("shed", "A small simple building used for storing tools.", "Garden tools and flower pots were kept in the wooden shed.", "SHED", "shed", "Saying 'shad' instead of short 'e'.", "A cozy wooden garden shed nestled behind green bushes"),
        ("well", "A deep shaft dug into the earth to obtain fresh water.", "The stone well provided cool, clear water for the town.", "WEL", "well", "Saying 'will' instead of short 'e'.", "A rustic stone water well with a wooden bucket and crank"),
        ("rope", "A strong thick cord made of twisted fiber strands.", "He tied the small wooden boat securely with a hemp rope.", "ROHP", "rope", "Saying 'rap' or 'rip'.", "A coiled length of sturdy natural hemp rope"),
        ("knot", "A fastening made by tying a piece of rope or string.", "She tied a sturdy square knot to secure the package.", "NAHT", "knot", "Pronouncing the silent 'k'.", "A neatly tied sailor knot in a thick rope"),
        ("clay", "A stiff, sticky fine-grained earth used for pottery.", "The potter shaped a beautiful round vase out of soft clay.", "KLAY", "clay", "Saying 'klee' instead of long 'a'.", "A spinning pottery wheel with wet terracotta clay shaped into a pot"),
    ],
    # L11: 5-letter initial blends (L-blends, R-blends)
    [
        ("clock", "A device that measures and displays the time of day.", "The grandfather clock chimed every hour.", "KLAHK", "clock", "Dropping the 'l' blend sound.", "An ornate antique wooden grandfather clock with a pendulum"),
        ("train", "A series of connected railway cars pulled by an engine.", "The passenger train rumbled smoothly along the tracks.", "TRAYN", "train", "Saying 'chrain' instead of crisp 'tr'.", "A modern passenger train traveling through a green countryside"),
        ("plant", "A living organism that absorbs water through its roots.", "She watered the green potted plant on the windowsill.", "PLANT", "plant", "Saying 'plent' or dropping 'l'.", "A thriving potted green houseplant with broad leaves"),
        ("spoon", "An eating utensil consisting of a small shallow bowl.", "He stirred the warm vegetable soup with a silver spoon.", "SPOON", "spoon", "Saying 'spun' instead of long 'oo'.", "A polished stainless steel soup spoon on a napkin"),
        ("bread", "A staple food made of baked flour dough and yeast.", "The baker sliced a warm loaf of crusty sourdough bread.", "BRED", "bread", "Pronouncing 'ea' as long 'e' (breed).", "A golden loaf of freshly baked artisan bread on a cutting board"),
        ("house", "A building designed for people to live in comfortably.", "Smoke rose gently from the chimney of the stone house.", "HOWSS", "house", "Saying 'howz' with voiced 'z'.", "A cozy countryside stone cottage house with flower boxes"),
        ("green", "The color between blue and yellow on the spectrum.", "Spring brought fresh green leaves to every village tree.", "GREEN", "green", "Saying 'grin' with short 'i'.", "A vibrant green shamrock leaf glowing in the sunlight"),
    ],
    # L12: 5-letter digraphs & common nouns
    [
        ("chair", "A piece of furniture with a back for one person to sit on.", "She sat in the wooden rocking chair near the fireplace.", "CHAIR", "chair", "Saying 'share' instead of 'ch' sound.", "A handcrafted wooden dining chair with a cushion"),
        ("water", "A clear liquid essential for all plant and animal life.", "Cool pure water flowed gently from the village spring.", "WAH-ter", "wa-ter", "Saying 'wader' with a sloppy 'd'.", "A clear glass filled with pure sparkling water with ice"),
        ("apple", "A round fruit with crisp flesh and red or green skin.", "She picked a sweet red apple directly from the orchard tree.", "AP-uhl", "ap-ple", "Saying 'ep-uhl' instead of short 'a'.", "A shiny red honeycrisp apple with a single green leaf"),
        ("table", "A piece of furniture with a flat top and legs.", "The family gathered around the wooden dining table for dinner.", "TAY-buhl", "ta-ble", "Saying 'teb-uhl' instead of long 'a'.", "A sturdy polished oak dining table set with plates"),
        ("grass", "Green vegetation consisting of short narrow leaves.", "Dewdrops glistened on the blades of morning grass.", "GRAS", "grass", "Saying 'grahs' or dropping 'r'.", "A field of fresh green lawn grass with morning dew"),
        ("sheep", "A domesticated mammal with a thick woolly fleece coat.", "The shepherd guided the flock of white sheep to pasture.", "SHEEP", "sheep", "Saying 'ship' with short 'i'.", "A fluffy white wool sheep grazing peacefully in a meadow"),
        ("horse", "A large majestic four-legged mammal with hooves and a mane.", "The brown horse trotted gracefully along the open path.", "HORS", "horse", "Saying 'hoarse' or dropping 'r'.", "A strong chestnut horse standing proudly in an open paddock"),
    ],
    # L13: 5-letter household & village items
    [
        ("truck", "A large heavy motor vehicle used for transporting goods.", "The delivery truck carried fresh produce to the village store.", "TRUHK", "truck", "Saying 'truk' with short 'oo'.", "A bright red pickup truck carrying crates of fresh vegetables"),
        ("fence", "A barrier of wooden posts or wire enclosing an area.", "A white picket fence bordered the colorful flower garden.", "FENS", "fence", "Saying 'fense' with a hard 's'.", "A neat white picket fence surrounding a garden of tulips"),
        ("bench", "A long sturdy seat for several people outdoors.", "We sat on the park bench to watch the birds in the square.", "BENCH", "bench", "Saying 'bansh' instead of 'ch'.", "A dark green wrought iron park bench under a shady elm tree"),
        ("brush", "An implement with bristles used for cleaning or painting.", "The artist dipped her paintbrush into bright blue paint.", "BRUHSH", "brush", "Saying 'broosh' with long 'oo'.", "A wooden artists paintbrush with colorful paint on the tip"),
        ("plate", "A flat dish from which food is served or eaten.", "She placed a warm slice of pie onto the ceramic plate.", "PLAYT", "plate", "Saying 'plet' with short 'e'.", "A clean white ceramic dinner plate with gold rim trim"),
        ("glass", "A hard transparent substance used for windows and cups.", "Sunlight streamed brightly through the clean glass window.", "GLAS", "glass", "Saying 'gless' instead of short 'a'.", "A transparent glass tumbler catching bright sunlight"),
        ("fork", "A handheld utensil with tines used for eating food.", "He picked up his salad using a polished stainless fork.", "FORK", "fork", "Dropping the 'r' coloring.", "A shiny stainless steel four-tine dinner fork"),
    ],
    # L14: 5-letter tools, clothing & materials
    [
        ("knife", "A cutting utensil with a sharp blade attached to a handle.", "The chef used a sharp kitchen knife to dice the carrots.", "NYF", "knife", "Pronouncing the silent initial 'k'.", "A professional chef cooking knife with a wooden handle"),
        ("towel", "An absorbent cloth used for drying hands, face, or body.", "She dried her hands with a soft fluffy cotton towel.", "TOW-uhl", "tow-el", "Saying 'tall' instead of two syllables.", "A folded stack of clean, soft cotton bathroom towels"),
        ("brick", "A rectangular block of baked clay used in building walls.", "Masons laid each red clay brick with mortar to build the wall.", "BRIK", "brick", "Saying 'breek' with long 'e'.", "A stack of traditional red clay building bricks"),
        ("stone", "Hard solid non-metallic mineral matter of rock.", "The ancient bridge was built entirely of sturdy grey stone.", "STOHN", "stone", "Saying 'ston' with short 'o'.", "A collection of smooth grey building stones fitted in a wall"),
        ("wheel", "A circular frame that revolves on an axle to move vehicles.", "The bicycle wheel turned smoothly along the paved trail.", "WEEL", "wheel", "Dropping the 'w/wh' aspiration.", "A spoked bicycle wheel with a black rubber tire"),
        ("shirt", "A garment for the upper body with sleeves and a collar.", "He wore a clean pressed cotton shirt for the celebration.", "SHURT", "shirt", "Saying 'short' instead of 'er' sound.", "A neatly buttoned light blue collared casual shirt"),
        ("dress", "A one-piece garment for women and girls with a skirt.", "She wore a lovely yellow summer dress with flower prints.", "DRES", "dress", "Saying 'drass' instead of short 'e'.", "A cheerful yellow floral summer dress hanging on a wooden hanger"),
    ],
    # L15: 5-letter clothing, animals, and tools
    [
        ("shoes", "Outer coverings for the human foot with a sturdy sole.", "He laced up his sturdy leather hiking shoes for the walk.", "SHOOZ", "shoes", "Saying 'shoos' with unvoiced 's'.", "A pair of clean brown leather lace-up walking shoes"),
        ("socks", "Soft garments worn on the feet inside shoes.", "She pulled on warm wool socks on a chilly morning.", "SAHKS", "socks", "Saying 'sox' with long 'o'.", "A pair of cozy knitted wool winter socks with patterns"),
        ("flock", "A group of birds or sheep that live and travel together.", "A large flock of geese flew in formation across the sky.", "FLAHK", "flock", "Saying 'flook' with long 'oo'.", "A flock of white birds flying together over a scenic meadow"),
        ("chick", "A young baby bird, especially a young chicken.", "The fluffy yellow chick peeped happily near its mother.", "CHIK", "chick", "Saying 'cheek' with long 'e'.", "An adorable fluffy yellow baby chick standing in straw"),
        ("puppy", "A young baby dog known for playfulness and loyalty.", "The playful brown puppy chased a tennis ball in the yard.", "PUHP-ee", "pup-py", "Saying 'pappy' instead of short 'u'.", "A cute golden retriever puppy with floppy ears and big eyes"),
        ("kitty", "An affectionate term for a young or small pet cat.", "The sweet striped kitty curled up warmly on the rug.", "KIT-ee", "kit-ty", "Saying 'ket-tee' with short 'e'.", "A tiny striped kitten playing with a soft yarn ball"),
        ("broom", "A cleaning tool with bristles attached to a long handle.", "She used a straw broom to sweep the stone kitchen floor.", "BROOM", "broom", "Saying 'brum' with short 'u'.", "A traditional wooden straw sweeping broom leaning against a wall"),
    ],
    # L16: 6-letter village places & architecture
    [
        ("market", "A public gathering place where food and goods are sold.", "Farmers sold fresh berries and honey at the weekend market.", "MAHR-kit", "mar-ket", "Dropping the second syllable 'et'.", "A vibrant outdoor farmers market with fruit and vegetable stalls"),
        ("street", "A public road in a city or village bordered by buildings.", "Cobblestone lanterns illuminated the quiet village street.", "STREET", "street", "Saying 'strit' with short 'i'.", "A charming European cobblestone village street with streetlamps"),
        ("garden", "A piece of ground used for growing flowers and plants.", "Colorful roses and sweet lavender bloomed in the garden.", "GAHR-duhn", "gar-den", "Saying 'gordin' with wrong vowel.", "A lush blooming flower garden with stepping stones"),
        ("window", "An opening in a wall fitted with glass to let in light.", "She opened the wooden window to let in the morning breeze.", "WIN-doh", "win-dow", "Saying 'win-der' or 'win-duh'.", "A sunny cottage window with open wooden shutters and flowers"),
        ("bridge", "A structure carrying a pathway or road across water.", "The stone bridge spanned gracefully over the river stream.", "BRIJ", "bridge", "Pronouncing 'dge' as 'g' or 'zh'.", "An arched stone footbridge crossing over a gentle clear stream"),
        ("castle", "A large fortified building from medieval history.", "The grand castle stood majestically atop the green cliff.", "KAS-uhl", "cas-tle", "Pronouncing the silent 't'.", "A majestic fairytale stone castle with towers and flags"),
        ("cottage", "A small, charming and cozy house in the countryside.", "Ivy climbed up the stone walls of the countryside cottage.", "KAH-tij", "cot-tage", "Saying 'cot-taj' with wrong ending.", "A picturesque thatched-roof English countryside cottage"),
    ],
    # L17: 6-letter institutions, nature & professions
    [
        ("orchard", "A piece of land planted with fruit trees.", "Ripe red cherries hung heavily in the sunny orchard.", "OR-cherd", "or-chard", "Saying 'or-card' with hard 'c'.", "Rows of apple and cherry trees in a sunlit green orchard"),
        ("bakery", "A shop where bread, cakes, and pastries are baked.", "The sweet smell of warm cinnamon rolls filled the bakery.", "BAY-kuh-ree", "bak-er-y", "Saying 'beck-uh-ree'.", "A cozy artisan bakery shop with loaves of bread on shelves"),
        ("school", "An institution where children learn and study together.", "The bell rang as students arrived happily at school.", "SKOOL", "school", "Saying 'sool' and dropping the 'k' sound.", "A friendly brick school building with a clocktower and playground"),
        ("church", "A building used for public religious worship and gatherings.", "The village church steeple rose gracefully above the trees.", "CHURCH", "church", "Saying 'shursh' instead of double 'ch'.", "A historic stone village church with stained glass windows"),
        ("doctor", "A qualified medical professional who helps people stay healthy.", "The kind doctor listened to her heartbeat with a stethoscope.", "DAHK-ter", "doc-tor", "Saying 'dok-tawr' with overstressed second syllable.", "A friendly doctor in a white coat holding a stethoscope"),
        ("farmer", "A person who operates a farm to grow crops and raise livestock.", "The hardworking farmer harvested golden wheat in the afternoon.", "FAHR-mer", "farm-er", "Dropping the 'r' coloring in both syllables.", "A smiling farmer in overalls standing in a golden wheat field"),
        ("driver", "A person who operates a vehicle such as a car or bus.", "The bus driver greeted every student with a warm smile.", "DRY-ver", "driv-er", "Saying 'dree-ver' with long 'e'.", "A friendly professional driver sitting behind a steering wheel"),
    ],
    # L18: 6-letter occupations & artisans
    [
        ("baker", "A person whose job is making bread, rolls, and cakes.", "The skilled baker shaped sourdough loaves with care.", "BAY-ker", "bak-er", "Saying 'backer' with short 'a'.", "A baker in a white apron pulling fresh bread from an oven"),
        ("grocer", "A person who sells food and household provisions.", "The neighborhood grocer weighed fresh apples on the scale.", "GROH-ser", "gro-cer", "Saying 'graw-cer' with short 'o'.", "A cheerful grocer arranging colorful citrus fruits on display"),
        ("butcher", "A person who prepares and sells meat products.", "The local butcher sliced fresh cuts of roast for dinner.", "BUCH-er", "butch-er", "Pronouncing 'u' as in 'but' instead of 'put'.", "A clean traditional butcher shop counter with hanging scales"),
        ("painter", "An artist who paints pictures or walls of buildings.", "The talented painter captured the sunset on her canvas.", "PAYN-ter", "paint-er", "Saying 'penn-ter' with short 'e'.", "An artist painting a landscape on an easel in a park"),
        ("tailor", "A person whose occupation is making and altering garments.", "The master tailor measured the sleeve of the wool coat.", "TAY-ler", "tai-lor", "Saying 'tie-lor' with long 'i'.", "A tailor measuring fabric with a yellow measuring tape"),
        ("cook", "A person who prepares food for others to eat.", "The restaurant cook seasoned the simmering soup with fresh herbs.", "KUK", "cook", "Saying 'kook' with long 'oo'.", "A professional cook in a chef hat stirring a copper pot"),
        ("worker", "A person who performs a specified job or labor.", "The construction worker wore a sturdy yellow safety helmet.", "WUR-ker", "work-er", "Saying 'war-ker' instead of 'er' sound.", "A hardworking worker in a bright safety vest and hardhat"),
    ],
    # L19: 6-letter family & community members
    [
        ("helper", "A person who contributes assistance or support to others.", "The little helper carried the grocery bag inside the house.", "HEL-per", "help-er", "Saying 'hal-per' with short 'a'.", "A helpful child helping carry a wicker basket of flowers"),
        ("neighbor", "A person living near or next door to another.", "Our friendly neighbor waved hello from across the garden.", "NAY-ber", "neigh-bor", "Pronouncing the silent 'gh'.", "Two friendly neighbors chatting warmly over a wooden fence"),
        ("friend", "A person with whom one has a bond of mutual affection.", "She shared her favorite storybook with her best friend.", "FREND", "friend", "Pronouncing 'ie' as long 'e' (freend).", "Two happy young friends hugging and laughing together"),
        ("family", "A group consisting of parents and children living together.", "The entire family gathered around the table for a feast.", "FAM-uh-lee", "fam-i-ly", "Rushing through the middle syllable.", "A happy loving family smiling together in a portrait"),
        ("cousin", "A child of one's uncle or aunt.", "He played tag with his favorite cousin during the summer visit.", "KUHZ-in", "cous-in", "Saying 'coo-sin' with long 'oo'.", "Two cousins laughing and playing a board game together"),
        ("sister", "A female sibling with the same parents.", "Her older sister helped her tie her shoelaces neatly.", "SIS-ter", "sis-ter", "Saying 'sees-ter' with long 'e'.", "Two loving sisters walking hand in hand in the park"),
        ("brother", "A male sibling with the same parents.", "His younger brother built a tall tower out of blocks.", "BRUH-ther", "broth-er", "Saying 'brah-ther' or dropping 'th'.", "Two brothers building a wooden block castle on a rug"),
    ],
    # L20: 6-letter village geography & settlements
    [
        ("parent", "A father or mother who nurtures and raises a child.", "Each parent cheered proudly at the school music concert.", "PAIR-uhnt", "par-ent", "Saying 'pah-rent' with short 'a'.", "A caring parent reading a bedtime story to their child"),
        ("infant", "A very young child or baby in the earliest stage of life.", "The peaceful infant slept soundly in the wooden crib.", "IN-fuhnt", "in-fant", "Over-pronouncing the second syllable as 'fant'.", "A sweet baby infant sleeping peacefully wrapped in a blanket"),
        ("toddler", "A young child who is just beginning to walk.", "The energetic toddler took his first steady steps on the rug.", "TAHD-ler", "tod-dler", "Saying 'toad-ler' with long 'o'.", "A cheerful toddler smiling while taking steps across a playroom"),
        ("village", "A group of houses and buildings in a rural area.", "Sunlight illuminated the colorful roofs of the quiet village.", "VIL-ij", "vil-lage", "Saying 'vil-layj' with wrong ending.", "A scenic panoramic view of a sunny hillside European village"),
        ("hamlet", "A small settlement generally smaller than a village.", "A tranquil hamlet nestled beside the peaceful river valley.", "HAM-lit", "ham-let", "Saying 'home-let' with long 'o'.", "A tiny rural hamlet of four stone cottages beside a meadow"),
        ("square", "An open typical four-sided area in a town or city.", "The town square featured a grand bubbling water fountain.", "SKWAIR", "square", "Saying 'skware' and dropping the 'kw' sound.", "A bustling open paved European town square with cafe tables"),
        ("plaza", "A public square or marketplace in a city or town.", "Children fed pigeons peacefully in the sunny village plaza.", "PLAH-zuh", "pla-za", "Saying 'play-zuh' with long 'a'.", "A wide sunlit open stone plaza surrounded by arched colonnades"),
    ],
    # L21: 7-letter municipal & civic structures
    [
        ("library", "A building containing collections of books and periodicals.", "She borrowed three fascinating nature books from the library.", "LY-brer-ee", "li-brar-y", "Saying 'ly-ber-ee' and skipping the first 'r'.", "A grand historic library room with tall oak bookshelves"),
        ("hospital", "An institution providing medical and surgical treatment.", "The modern hospital provided skilled medical care around the clock.", "HAHS-pi-tuhl", "hos-pi-tal", "Skipping the middle 'pi' syllable.", "A clean modern brick hospital building with an entrance canopy"),
        ("station", "A regular stopping place on a public transport route.", "Passengers waited on the clean platform at the train station.", "STAY-shuhn", "sta-tion", "Saying 'stat-shun' with short 'a'.", "A classic railway train station platform with vintage lamps"),
        ("fountain", "An ornamental structure in a pool from which water spouts.", "Coins shimmered at the bottom of the town fountain.", "FOWN-tuhn", "foun-tain", "Saying 'fown-tayn' with long 'a'.", "A beautiful carved stone fountain spraying crystal clear water"),
        ("chimney", "A vertical channel carrying smoke up through the roof.", "Wisps of white woodsmoke drifted gently from the brick chimney.", "CHIM-nee", "chim-ney", "Saying 'shim-nee' instead of 'ch'.", "A sturdy red brick chimney rising above slate cottage roof tiles"),
        ("rooftop", "The outer surface of a building's roof.", "Weathervanes spun in the breeze atop the sunny rooftop.", "ROOF-tahp", "roof-top", "Saying 'ruf-tap' with short 'u'.", "A terracotta tiled cottage rooftop overlooking a green valley"),
        ("balcony", "A platform enclosed by a railing projecting from a wall.", "Potted geraniums hung brightly from the second-floor balcony.", "BAL-kuh-nee", "bal-co-ny", "Saying 'bol-co-nee' with wrong vowel.", "A charming wrought iron flower balcony on a stone village townhouse"),
    ],
    # L22: 7-letter transport & thoroughfares
    [
        ("pathway", "A path or way providing access between locations.", "A winding pathway bordered with stepping stones led to the lake.", "PATH-way", "path-way", "Saying 'pet-way' or mispronouncing 'th'.", "A winding stone pathway bordered by colorful lavender bushes"),
        ("sidewalk", "A paved pedestrian walkway at the side of a street.", "Children rode their scooters safely along the neighborhood sidewalk.", "SYD-wawk", "side-walk", "Pronouncing the silent 'l' in walk.", "A clean concrete pedestrian sidewalk lined with shady street trees"),
        ("crosswalk", "A marked part of a road where pedestrians have right of way.", "The crossing guard helped students walk across the white crosswalk.", "KRAWS-wawk", "cross-walk", "Dropping the 'cr' blend.", "White painted zebra stripes of a crosswalk on a quiet street"),
        ("traffic", "Vehicles moving on a public highway or road network.", "The polite village traffic moved at a gentle, safe pace.", "TRAF-ik", "traf-fic", "Saying 'traff-eek' with long 'e'.", "Bicycles and colorful cars moving smoothly along a village avenue"),
        ("bicycle", "A vehicle composed of two wheels held in a frame.", "He rode his blue bicycle along the riverside bike path.", "BY-si-kuhl", "bi-cy-cle", "Saying 'bike-si-cle' with hard 'k'.", "A classic vintage cruiser bicycle leaning against a stone wall"),
        ("scooter", "A light two-wheeled vehicle with a low footboard.", "She glided smoothly on her red kick scooter down the pavement.", "SKOO-ter", "scoot-er", "Saying 'skut-ter' with short 'u'.", "A bright red aluminum two-wheel kick scooter with handlebars"),
        ("carriage", "A four-wheeled horse-drawn passenger vehicle.", "The polished royal carriage carried guests through the park.", "KAIR-ij", "car-riage", "Saying 'car-ree-aj' with wrong ending.", "An elegant black horse-drawn passenger carriage with wooden wheels"),
    ],
    # L23: 7-letter agriculture & rural landscape
    [
        ("wagon", "A heavy four-wheeled vehicle used for transporting goods.", "The team of draft horses pulled the wooden wagon of hay.", "WAG-uhn", "wag-on", "Saying 'way-gon' with long 'a'.", "A sturdy wooden farm wagon loaded with fresh golden hay"),
        ("tractor", "A powerful motor vehicle with large rear tires for farms.", "The green tractor plowed deep furrows across the field.", "TRAK-ter", "trac-tor", "Saying 'trak-tawr' with overstressed ending.", "A bright green agricultural tractor working in a farm field"),
        ("windmill", "A building with sails or vanes turned by the wind.", "The historic Dutch windmill ground grain into flour with the breeze.", "WIND-mil", "wind-mill", "Saying 'wynd-mill' with long 'i'.", "A traditional wooden windmill with large spinning canvas sails"),
        ("waterfall", "A cascade of water falling from a height over rocks.", "Cool mist rose from the base of the mountain waterfall.", "WAH-ter-fawl", "wa-ter-fall", "Pronouncing with sloppy vowels.", "A scenic mountain waterfall cascading over mossy granite boulders"),
        ("stream", "A small, narrow river of clean flowing freshwater.", "Silvery trout darted through the shallow pebble stream.", "STREEM", "stream", "Saying 'shtream' with 'sh' sound.", "A crystal-clear shallow stream flowing over smooth pebbles"),
        ("meadow", "A piece of grassland used for pasture or wildflowers.", "Butterflies fluttered across the colorful summer meadow.", "MED-oh", "mead-ow", "Pronouncing 'ea' as long 'e' (mee-dow).", "A lush green countryside meadow blooming with yellow and purple wildflowers"),
        ("pasture", "Land covered with grass suitable for grazing animals.", "Dairy cattle grazed contentedly in the fenced green pasture.", "PAS-cher", "pas-ture", "Saying 'pas-tyoor' with unnatural stress.", "A wide green pasture under an open blue sky with distant hills"),
    ],
    # L24: 7-letter farm tools & homestead items
    [
        ("haystack", "A large packed stack of hay stored in a farm field.", "The golden haystack stood dry and tall beside the barn door.", "HAY-stak", "hay-stack", "Saying 'hay-stek' with short 'e'.", "A traditional round dome-shaped golden haystack in a field"),
        ("scarecrow", "A figure of a person dressed in old clothes to scare birds.", "The friendly straw scarecrow stood guard in the corn patch.", "SKAIR-kroh", "scare-crow", "Saying 'scar-crow' with wrong vowel.", "A cheerful stuffed scarecrow wearing a floppy hat in a cornfield"),
        ("plow", "A large farming implement with blades to turn over soil.", "The sharp iron plow turned rich dark soil for spring planting.", "PLOW", "plow", "Saying 'plo' with long 'o'.", "A traditional cast iron farming plow resting in tilled soil"),
        ("shovel", "A tool with a broad blade used for lifting and moving coal or soil.", "He used a sturdy metal shovel to plant the young oak sapling.", "SHUHV-uhl", "shov-el", "Saying 'show-vel' with long 'o'.", "A sturdy steel digging shovel with a smooth wooden handle"),
        ("bucket", "A cylindrical vessel with a handle used for carrying liquids.", "She carried a wooden bucket of fresh well water to the kitchen.", "BUHK-it", "buck-et", "Saying 'book-et' with long 'oo'.", "A traditional wooden water bucket with a metal handle"),
        ("lantern", "A lamp with a transparent case protecting the flame inside.", "The brass lantern cast a cozy warm glow on the porch.", "LAN-tern", "lan-tern", "Saying 'len-tern' with short 'e'.", "An antique brass lantern with a glowing candle flame inside"),
        ("candle", "A cylinder of wax with a central wick that burns for light.", "A scented vanilla candle flickered gently on the mantelpiece.", "KAN-duhl", "can-dle", "Saying 'ken-duhl' with short 'e'.", "A burning pillar candle on a ceramic dish casting a soft glow"),
    ],
    # L25: 7-letter household furnishings
    [
        ("blanket", "A large piece of woolen or cotton material used for warmth.", "She snuggled under a soft quilted blanket by the fire.", "BLANG-kit", "blan-ket", "Saying 'blen-ket' with short 'e'.", "A folded cozy knit woolen blanket resting on the edge of a bed"),
        ("pillow", "A rectangular cushion used to support the head in bed.", "He rested his head on a soft feather pillow.", "PIL-oh", "pil-low", "Saying 'pel-low' with short 'e'.", "A fluffy white cotton bed pillow with clean linen"),
        ("curtain", "A piece of hanging cloth used to drape a window.", "Sunlight filtered through the white lace window curtain.", "KUR-tuhn", "cur-tain", "Saying 'cur-tayn' with long 'a'.", "Elegant white lace window curtains billowing gently in a breeze"),
        ("cabinet", "A cupboard with drawers or shelves for storing objects.", "Fine ceramic teacups were displayed inside the glass cabinet.", "KAB-i-nit", "cab-i-net", "Skipping the middle 'i' syllable.", "A handsome polished wooden kitchen display cabinet with glass doors"),
        ("dresser", "A low chest of drawers for storing folded clothes.", "She kept her warm sweaters in the top drawer of the oak dresser.", "DRES-er", "dress-er", "Saying 'drass-er' with short 'a'.", "A classic wooden bedroom chest of drawers with brass knobs"),
        ("cupboard", "A piece of furniture with doors used for storing dishes or food.", "He took a clean bowl from the kitchen cupboard.", "KUHB-erd", "cup-board", "Pronouncing the silent 'p' as 'cup-board'.", "A painted kitchen cupboard with wooden shelves filled with plates"),
        ("hallway", "A passageway in a building onto which rooms open.", "Family photographs lined the warm wooden walls of the hallway.", "HAWL-way", "hall-way", "Saying 'hell-way' with short 'e'.", "A welcoming wooden hallway corridor with framed pictures on the wall"),
    ],
    # L26: 8+ letter community & civic life
    [
        ("community", "A group of people living in the same place with shared goals.", "The village community joined together to build the new playground.", "kuh-MYOO-ni-tee", "com-mu-ni-ty", "Saying 'co-moo-ni-ty' with wrong stress.", "A diverse group of smiling neighbors working together in a garden"),
        ("neighborhood", "A district or community within a town or suburb.", "Trees lined the peaceful streets of the friendly neighborhood.", "NAY-ber-hud", "neigh-bor-hood", "Skipping the middle syllable 'bor'.", "A pleasant suburban neighborhood street with gardens and houses"),
        ("playground", "An outdoor area provided for children to play on.", "Children laughed as they took turns on the playground swings.", "PLAY-grownd", "play-ground", "Dropping the final 'nd' blend.", "A colorful community playground with slides, swings, and climbing bars"),
        ("supermarket", "A large self-service grocery store selling diverse goods.", "They bought fresh fruits and artisan cheeses at the supermarket.", "SOO-per-mahr-kit", "su-per-mar-ket", "Skipping the middle 'per' syllable.", "A brightly lit modern supermarket aisle filled with fresh food"),
        ("courthouse", "A building in which a judicial court of law is held.", "Stone pillars framed the entrance of the historic courthouse.", "KORT-howss", "court-house", "Saying 'cort-howz' with voiced 'z'.", "A dignified classical stone courthouse with majestic columns"),
        ("postoffice", "A public department responsible for mail and parcel delivery.", "He dropped his handwritten letter into the slot at the post office.", "POHST-aw-fis", "post-of-fice", "Slurring the two words together awkwardly.", "A traditional red brick post office building with a mail drop box"),
        ("firehouse", "A station where fire engines are housed and firefighters work.", "The shiny red fire truck was parked ready inside the firehouse.", "FYR-howss", "fire-house", "Saying 'fire-howz' with voiced 'z'.", "A classic municipal firehouse with tall red bay doors"),
    ],
    # L27: 8+ letter residential & historical architecture
    [
        ("clocktower", "A tall tower typically with four clock faces on its top.", "The village clock tower chimed four resonant bells across the valley.", "KLAHK-tow-er", "clock-tow-er", "Skipping the middle 'k' sound.", "A majestic historic stone clock tower rising into a blue sky"),
        ("townhouse", "A tall, narrow traditional terraced house in a city.", "Flowering ivy framed the brick front of the Victorian townhouse.", "TOWN-howss", "town-house", "Saying 'town-howz' with voiced 'z'.", "A stately brick Victorian townhouse with a front stone staircase"),
        ("apartment", "A suite of rooms forming one separate residence.", "They enjoyed a wonderful view of the park from their sunny apartment.", "uh-PAHRT-muhnt", "a-part-ment", "Saying 'ap-part-e-ment' with extra syllable.", "A modern urban apartment living room with tall scenic windows"),
        ("residence", "A person's home; the place where someone lives.", "The historic stone residence was preserved with great care.", "REZ-i-duhns", "res-i-dence", "Saying 'res-i-dants' with hard 't'.", "An elegant historic residential stone home with landscaped gardens"),
        ("homestead", "A farmhouse and the adjoining land surrounding it.", "Pioneers established a thriving homestead on the prairie.", "HOHM-sted", "home-stead", "Saying 'home-stid' with wrong vowel.", "A historic rural wooden homestead farmhouse surrounded by green pastures"),
        ("settlement", "An official place where people establish a community.", "Early settlers built a peaceful farming settlement beside the river.", "SET-uhl-muhnt", "set-tle-ment", "Rushing through the middle 'tle' syllable.", "An early wooden pioneer settlement with log cabins and fences"),
        ("blacksmith", "A metalsmith who creates objects from wrought iron or steel.", "The sturdy blacksmith forged an iron horseshoe over the glowing anvil.", "BLAK-smith", "black-smith", "Mispronouncing unvoiced 'th' at the end.", "A traditional blacksmith in a leather apron hammering glowing iron"),
    ],
    # L28: 8+ letter artisan trades & public services
    [
        ("carpenter", "A person who builds or repairs wooden structures.", "The master carpenter measured oak planks to build a bookshelf.", "KAHR-pen-ter", "car-pen-ter", "Saying 'car-pin-ter' with short 'i'.", "A skilled woodworker carpenter smoothing a wooden board with a hand plane"),
        ("shoemaker", "A person who makes and repairs leather footwear.", "The skilled shoemaker stitched durable soles onto the leather boots.", "SHOO-may-ker", "shoe-ma-ker", "Saying 'sho-maker' with short 'o'.", "A traditional shoemaker workshop with leather boots and cobbler tools"),
        ("gardener", "A person who tends and cultivates a garden.", "The dedicated gardener pruned the fragrant red rose bushes.", "GAHRD-ner", "gar-den-er", "Over-pronouncing into four awkward syllables.", "A smiling gardener with pruning shears tending a bed of colorful roses"),
        ("shopkeeper", "An owner or manager of a retail shop.", "The friendly shopkeeper greeted every customer who walked inside.", "SHAHP-kee-per", "shop-keep-er", "Saying 'chop-keeper' with 'ch'.", "A cheerful shopkeeper standing behind an old-fashioned wooden store counter"),
        ("innkeeper", "A person who owns or manages a countryside inn.", "The hospitable innkeeper offered warm soup and a comfortable room.", "IN-kee-per", "inn-keep-er", "Saying 'een-keeper' with long 'e'.", "A welcoming innkeeper holding a brass room key in a rustic lobby"),
        ("policeman", "A male police officer dedicated to public safety.", "The courteous policeman helped the lost puppy find its owner.", "puh-LEES-muhn", "po-lice-man", "Saying 'pole-iss-man' with wrong stress.", "A friendly police officer in uniform standing on a sunny street corner"),
        ("fireman", "A firefighter who extinguishes destructive fires.", "The brave fireman carried a high-pressure water hose into the building.", "FYR-muhn", "fire-man", "Saying 'far-man' with dropped vowel.", "A brave firefighter in protective yellow gear holding a brass hose nozzle"),
    ],
    # L29: 8+ letter transport & civic roles
    [
        ("mailman", "A mail carrier who delivers letters and packages.", "The punctual mailman placed the morning letters in our mailbox.", "MAYL-muhn", "mail-man", "Saying 'mel-man' with short 'e'.", "A friendly mail carrier in uniform placing a letter in a blue mailbox"),
        ("pharmacist", "A licensed professional qualified to prepare medications.", "The knowledgeable pharmacist explained how to take the medicine.", "FAHR-muh-sist", "phar-ma-cist", "Saying 'far-ma-kist' with hard 'c'.", "A professional pharmacist in a lab coat checking medicine bottles"),
        ("librarian", "A person in charge of managing books in a library.", "The helpful librarian guided her to the encyclopedia section.", "ly-BRAIR-ee-uhn", "li-brari-an", "Skipping the 'r' in the second syllable.", "A friendly librarian organizing books onto wooden library shelves"),
        ("pedestrian", "A person walking along a street or road.", "Drivers stopped politely to let each pedestrian cross the avenue.", "puh-DES-tree-uhn", "pe-des-tri-an", "Saying 'ped-es-tran' with dropped syllable.", "Pedestrians walking safely along a wide scenic city sidewalk"),
        ("commuter", "A person who travels some distance to work regularly.", "The busy commuter read the newspaper during the morning train ride.", "kuh-MYOO-ter", "com-mu-ter", "Saying 'com-moo-ter' with wrong vowel.", "A commuter holding a briefcase boarding a morning passenger train"),
        ("passenger", "A traveler on a public or private conveyance.", "Every passenger fastened their seatbelt before the flight took off.", "PAS-in-jer", "pas-sen-ger", "Saying 'pass-en-ger' with hard 'g'.", "A smiling passenger looking out the window of a train"),
        ("gathering", "An assembly or meeting of people for a purpose.", "The festive family gathering featured laughter, music, and food.", "GATH-er-ing", "gath-er-ing", "Mispronouncing the voiced 'th' sound.", "A joyous gathering of friends and family sharing dinner around a long table"),
    ],
    # L30: 8+ letter celebrations, heritage & village culmination
    [
        ("festival", "A day or period of celebration with performances and food.", "Colorful lanterns illuminated the annual village harvest festival.", "FES-tuh-vuhl", "fes-ti-val", "Saying 'fes-tee-vahl' with wrong stress.", "A vibrant outdoor festival with colorful banners, lanterns, and food stalls"),
        ("celebration", "The action of marking an important event or achievement.", "Cheers filled the square during the victory celebration.", "sel-uh-BRAY-shuhn", "cel-e-bra-tion", "Saying 'sel-bray-shun' with dropped syllable.", "A joyous celebration with confetti, balloons, and smiling people cheering"),
        ("ceremony", "A formal religious or public occasion celebrating an event.", "The graduation ceremony honored the hard work of every student.", "SAIR-uh-moh-nee", "cer-e-mo-ny", "Saying 'sair-mo-ny' with dropped syllable.", "A dignified formal ceremony with candles and ribbon cutting on a stage"),
        ("tradition", "The transmission of customs or beliefs from generation to generation.", "Baking apple pies in autumn was a cherished family tradition.", "truh-DISH-uhn", "tra-di-tion", "Saying 'tray-di-shun' with long 'a'.", "A grandmother teaching her grandchild a traditional baking recipe"),
        ("heritage", "Valued objects, traditions, and qualities passed down.", "The historic stone monuments formed an important part of their heritage.", "HAIR-i-tij", "her-i-tage", "Saying 'her-i-taj' with wrong ending.", "An ancient stone archway preserving architectural heritage in a village"),
        ("monument", "A statue, building, or structure built to commemorate a person.", "A bronze monument honored the founders of the historic village.", "MAHN-yuh-muhnt", "mon-u-ment", "Saying 'moan-u-ment' with long 'o'.", "A grand carved stone monument in a park plaza celebrating history"),
        ("adventure", "An exciting or daring experience of discovery and learning.", "They set out together on an unforgettable pronunciation adventure.", "ad-VEN-cher", "ad-ven-ture", "Saying 'ad-ven-toor' with unnatural ending.", "Two young adventurers with backpacks and a compass on a scenic trail"),
    ],
]
