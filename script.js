document.addEventListener('DOMContentLoaded', () => {
    const menuIcon = document.querySelector('.menu-icon');
    const navLinks = document.querySelector('.nav-links');
    const eventCards = document.querySelectorAll('.card');

    // Toggle mobile menu
    menuIcon.addEventListener('click', () => {
        navLinks.classList.toggle('active');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!menuIcon.contains(e.target) && !navLinks.contains(e.target)) {
            navLinks.classList.remove('active');
        }
    });

    // Filter events based on sport category
    const filterEvents = (selectedSport) => {
        console.log(`Filtering events for sport: ${selectedSport}`); // Debug log
        eventCards.forEach(card => {
            const sport = card.getAttribute('data-sport').toLowerCase();
            console.log(`Checking card with sport: ${sport}`); // Debug log
            if (selectedSport === 'all' || sport === selectedSport) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    };

    // Add click event listeners to navigation links
    document.querySelectorAll('nav ul li a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault(); // Prevent default anchor behavior

            const selectedSport = link.dataset.sport.toLowerCase();

            // Close the mobile menu after selecting a sport
            navLinks.classList.remove('active');

            // Filter events based on the selected sport
            filterEvents(selectedSport);
        });
    });

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase().trim();

        eventCards.forEach(card => {
            const title = card.querySelector('h3').textContent.toLowerCase();
            const teams = card.querySelector('.teams').textContent.toLowerCase();
            const channels = card.querySelector('.channels').textContent.toLowerCase();

            if (title.includes(query) || teams.includes(query) || channels.includes(query)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });

    // Initialize with all events visible
    filterEvents('all');
});
