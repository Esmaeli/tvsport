import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

# لیست ورزش‌های پشتیبانی‌شده
SUPPORTED_SPORTS = {
    "soccer", "cricket", "field hockey", "tennis", "boxing", 
    "wwe", "basketball", "handball", "lacrosse", "volleyball", "hockey"
}

def convert_to_tehran_time(uk_time_str):
    """ تبدیل زمان UK به ساعت تهران """
    if uk_time_str.strip() == "":
        return None
    uk_time = datetime.strptime(uk_time_str, "%H:%M")
    tehran_time = uk_time + timedelta(hours=3, minutes=30)
    return tehran_time.strftime("%H:%M")

def normalize_sport_name(sport_name):
    """ نرمال‌سازی نام ورزش """
    if 'hockey' in sport_name:
        return 'hockey'
    elif 'wwe' in sport_name:
        return 'wwe'
    elif 'tennis' in sport_name:
        return 'tennis'
    else:
        # حذف فضاهای اضافی و استاندارد کردن نام
        return sport_name.strip().lower()

def extract_sport_from_tag(tag):
    """ استخراج ورزش از تگ‌های <h2> یا <b> """
    if tag.name == 'h2':
        sport = tag.get_text(strip=True).lower()
        return normalize_sport_name(sport)
    elif tag.name == 'b':
        # بررسی کلاس تگ <b>
        sport_class = tag.get('class', [''])[0].lower()
        if any(s in sport_class for s in SUPPORTED_SPORTS):
            return normalize_sport_name(sport_class)
        
        # بررسی متن داخل تگ <b>
        sport_text = tag.get_text(strip=True).lower()
        if any(s in sport_text for s in SUPPORTED_SPORTS):
            return normalize_sport_name(sport_text)
    
    return None

def extract_event_info(url):
    """ استخراج اطلاعات رویدادها از صفحه وب """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    events = []
    strong_tags = soup.find_all('strong')
    
    for tag in strong_tags:
        event_text = ''.join(tag.find_all(text=True, recursive=False)).strip()
        
        time = event_text.split()[0]
        time = ''.join([char for char in time if char.isdigit() or char == ':'])
        
        tehran_time = convert_to_tehran_time(time)
        if tehran_time is None:
            continue
        
        rest_of_text = ' '.join(event_text.split()[1:])
        
        if ':' in rest_of_text:
            league = rest_of_text.split(':')[0].strip()
            teams_part = rest_of_text.split(':')[1].strip()
        else:
            league = rest_of_text
            teams_part = ''
        
        # اگر بخش تیم‌ها خالی باشد و هیچ توضیحی نداشته باشد، این رویداد را نادیده بگیر
        if not teams_part.strip() and not league.strip():
            continue
        
        # تشخیص نوع رویداد: دو تیمی یا تک‌نفره/ایونت
        is_single_event = True
        team_left, team_right = '', ''
        separators = [r'\s*vs\s*', r'\s*\.vs\s*', r'\s*x\s*']
        for separator in separators:
            if re.search(separator, teams_part):
                is_single_event = False
                teams = re.split(separator, teams_part)
                if len(teams) == 2:
                    team_left = teams[0].strip()
                    team_right = teams[1].strip()
                break
        
        channels = []
        for a in tag.find_all('a'):
            channel_text = a.get_text(strip=True)
            channel_text = channel_text.split('(')[0].strip()
            channels.append(channel_text)
        
        sport = None
        parent = tag.find_parent()
        if parent:
            h2_tag = parent.find_previous_sibling('h2')
            if h2_tag:
                sport = extract_sport_from_tag(h2_tag)
            
            if not sport:
                b_tag = parent.find_previous_sibling('b')
                if b_tag:
                    sport = extract_sport_from_tag(b_tag)
        
        if not sport:
            sport = league.split(' - ')[0].lower()
            sport = normalize_sport_name(sport)
        
        if sport in SUPPORTED_SPORTS:
            if is_single_event:
                # حالت تک‌نفره/ایونت: فقط ساعت، لیگ، و کانال‌ها
                event = {
                    'time': tehran_time,
                    'league': league,
                    'event_name': teams_part if teams_part.strip() else "Event",
                    'channels': channels,
                    'sport': sport,
                    'is_single_event': True
                }
            else:
                # حالت دو تیمی: شامل تیم‌ها
                event = {
                    'time': tehran_time,
                    'league': league,
                    'team_left': team_left,
                    'team_right': team_right,
                    'channels': channels,
                    'sport': sport,
                    'is_single_event': False
                }
            events.append(event)
    
    return events

def generate_main_content(events):
    """ تولید محتوای <main> برای HTML """
    main_content = '''
    <main>
        <div class="container">
            <section id="events">
                <h2>Today's Events</h2>
                <div class="event-cards">
    '''
    
    for event in events:
        if event['is_single_event']:
            # قالب‌بندی برای رویدادهای تک‌نفره/ایونت
            main_content += f'''
            <div class="card single-event" data-sport="{event['sport']}">
                <h3>{event['league']}</h3>
                <p class="event-name">{event.get('event_name', '')}</p>
                <p class="time">⏰ {event['time']} GMT</p>
                <p class="channels">Channels: {', '.join(event['channels'])}</p>
            </div>
            '''
        else:
            # قالب‌بندی برای رویدادهای دو تیمی
            main_content += f'''
            <div class="card" data-sport="{event['sport']}">
                <h3>{event['league']}</h3>
                <div class="teams">
                    <span class="team-left">{event['team_left']}</span>
                    <span class="vs">vs</span>
                    <span class="team-right">{event['team_right']}</span>
                </div>
                <p class="time">⏰ {event['time']} GMT</p>
                <p class="channels">Channels: {', '.join(event['channels'])}</p>
            </div>
            '''
    
    main_content += '''
                </div>
            </section>
        </div>
    </main>
    '''
    
    return main_content

def generate_complete_html(main_content):
    """ تولید سند HTML کامل """
    complete_html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sportify - Your Sports Events Hub</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- Header Section -->
    <header>
        <div class="container">
            <h1>Sportify</h1>
            <!-- Hamburger Menu Icon for Mobile -->
            <div class="menu-icon">
                ☰
            </div>
            <nav>
                <ul class="nav-links">
                    <li><a href="#" data-sport="all">All</a></li>
                    <li><a href="#" data-sport="soccer">Soccer</a></li>
                    <li><a href="#" data-sport="cricket">Cricket</a></li>
                    <li><a href="#" data-sport="field-hockey">Field Hockey</a></li>
                    <li><a href="#" data-sport="tennis">Tennis</a></li>
                    <li><a href="#" data-sport="boxing">Boxing</a></li>
                    <li><a href="#" data-sport="wwe">WWE</a></li>
                    <li><a href="#" data-sport="basketball">Basketball</a></li>
                    <li><a href="#" data-sport="handball">Handball</a></li>
                    <li><a href="#" data-sport="lacrosse">Lacrosse</a></li>
                    <li><a href="#" data-sport="volleyball">Volleyball</a></li>
                    <li><a href="#" data-sport="hockey">Hockey</a></li>
                </ul>
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Search events...">
                </div>
            </nav>
        </div>
    </header>
    <!-- Main Content Section -->
    {main_content}
    <!-- Footer Section -->
    <footer>
        <div class="container">
            <p>&copy; 2025 Sportify. All rights reserved.</p>
        </div>
    </footer>
    <script src="script.js"></script>
</body>
</html>
'''
    return complete_html

# اجرای کد
if __name__ == "__main__":
    url = 'http://time4tv.top/schedule.php'  # URL سایت
    events = extract_event_info(url)
    main_content = generate_main_content(events)
    complete_html = generate_complete_html(main_content)
    
    # ذخیره فایل index.html
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(complete_html)
    
    print("HTML file generated successfully!")
