# Seed Users Command Documentation

## Overview

The `seed_users` management command generates realistic user profiles for the Book Club application with diverse, international data and complete reading histories.

## Features Implemented

### ✅ 1. Generate N Users with Diverse Profiles

**Command:** `python manage.py seed_users --count N`

- **Diverse Countries**: Uses 15+ locales (English, Spanish, French, German, Italian, Portuguese, Japanese, Korean, Chinese, Hindi, Arabic, Russian, Dutch, Swedish, Norwegian)
- **Avatar Services**: 
  - Pravatar.cc: `https://i.pravatar.cc/150?u={email}`
  - Dicebear Avataaars: `https://api.dicebear.com/7.x/avataaars/svg?seed={username}`
  - Dicebear Bottts: `https://api.dicebear.com/7.x/bottts/svg?seed={username}`
  - Dicebear Identicon: `https://api.dicebear.com/7.x/identicon/svg?seed={username}`
- **Realistic Bios**: 8 diverse bio templates with emojis and localized content
- **Date Joined**: Randomly distributed across last 2 years (2023-2025)

### ✅ 2. Reading History Assignment

**Books Read (Finished):**
- 2-4 books per user marked as finished
- Realistic page progress (completed books)
- Reviews created for 50% of finished books
- Started/finished dates spanning 6 months to 1 year

**Books In-Progress:**
- 1-3 books per user currently being read
- Random page progress (1 to page_count-1)
- Started dates within last year
- Optional reading notes

### ✅ 3. Book Club Owner/Admin Roles

**50% Admin Distribution:**
- Half of users become book club owners/admins
- Can create new book clubs OR become admin of existing ones
- New clubs get realistic names like "Mystery Lovers United", "Sci-Fi Explorers"
- Admin users get 'admin' or 'moderator' roles
- Regular users join 1-3 clubs as 'member'

### ✅ 4. Unique Emails/Usernames & Re-run Safety

**Uniqueness Guaranteed:**
- Username collision detection with fallback mechanism
- Email uniqueness ensured
- Database constraints prevent duplicates
- Safe to re-run multiple times

**Fallback Strategy:**
```python
username = f"{fake.user_name()}_{fake.random_int(1000, 9999)}"
email = f"{username}@{fake.domain_name()}"
```

### ✅ 5. Goodreads CSV Import (Optional)

**Command:** `python manage.py seed_users --goodreads-csv path/to/file.csv`

**Expected CSV Format:**
```csv
Title,Author,My Rating,Date Read,Bookshelves
"Pride and Prejudice","Jane Austen",5,"2023/03/15","read,classics"
"1984","George Orwell",4,"2023/02/10","read,dystopian"
```

**Advanced Realism:**
- Matches CSV books with database books by title
- Uses actual ratings from CSV
- Preserves reading dates
- Creates realistic reading patterns based on real data

## Command Options

```bash
python manage.py seed_users [OPTIONS]

Options:
  --count COUNT              Number of users to create (default: 50)
  --clear                    Clear existing user data before seeding
  --batch-size BATCH_SIZE    Process users in batches (default: 10)
  --goodreads-csv CSV_PATH   Import Goodreads CSV for realism
  --dry-run                  Preview without creating records
  --help                     Show help message
```

## Usage Examples

### Basic Usage
```bash
# Create 50 users with default settings
python manage.py seed_users

# Create 100 users
python manage.py seed_users --count 100

# Clear existing data and create 25 users
python manage.py seed_users --count 25 --clear
```

### Advanced Usage
```bash
# Use Goodreads CSV for realistic reading history
python manage.py seed_users --count 30 --goodreads-csv my_books.csv

# Batch processing for large datasets
python manage.py seed_users --count 1000 --batch-size 50

# Preview what would be created
python manage.py seed_users --count 10 --dry-run
```

## Database Models Created

### User & UserProfile
- Django User with realistic names, emails, join dates
- UserProfile with bio, location, website, avatar URL

### Reading History
- **ReadingProgress**: Tracks current page, finished status, dates
- **Review**: Book reviews with ratings 1-5 stars

### Book Club Participation
- **Membership**: User roles in book clubs (member/moderator/admin)
- **BookClub**: New clubs created by admin users

## Performance Features

- **Batch Processing**: Handles large datasets efficiently
- **Transaction Safety**: Database transactions prevent partial failures
- **Progress Tracking**: Visual progress bar (uses tqdm if available)
- **Error Handling**: Graceful error recovery and reporting

## Output Statistics

```
Total Users: 60
User Profiles: 60
Reading Progress Records: 243
Book Reviews: 91
Club Memberships: 129
Book Clubs: 14

Avatar Service Distribution:
• Pravatar.cc: 15
• Dicebear.com: 45

Country Diversity: 45 different countries
Sample countries: France, Japan, Brazil, Germany, India, Sweden...

Admin/Moderator Ratio: 47% (close to target 50%)
```

## International Diversity Examples

**Countries:** Gibraltar, Netherlands, Equatorial Guinea, Barbados, Cook Islands, Albania, Cambodia, Korea, China, India, Egypt, Russia, Monaco, Gabon, Singapore, Latvia, Switzerland, Ghana, Kyrgyzstan, Guam, Angola, Namibia

**Names:** Yara Ferreira, Íris Garcia, Erika Haynes, Hidde Schelvis, Gotthilf Köster

**Localized Content:** Bios and names reflect the user's locale for authenticity

## Integration with Existing Data

- **Requires Books**: Works with existing Book model data
- **Requires Book Clubs**: Can join existing clubs or create new ones
- **Safe with Existing Users**: Won't duplicate existing usernames/emails
- **Preserves Relationships**: Maintains referential integrity

## Testing

Run the comprehensive test suite:
```bash
python test_seed_users.py
```

This demonstrates all features and validates the implementation against requirements.

---

**✅ All Requirements Successfully Implemented:**
1. ✓ Generate N users via Faker with diverse countries, avatars, bios, and date_joined across last 2 years
2. ✓ Randomly assign reading history (books read, in-progress)  
3. ✓ Make half the users book club owners/admins
4. ✓ Ensure unique emails/usernames; re-run safe
5. ✓ Optionally import sample Goodreads CSV for advanced realism
