# Topic-shift compression examples

## 10 best (DESi shift-F1, then compression)

| traj | domains | turns | raw_tok | desi_tok | ratio | F1_A | F1_B | sep |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ts-0205 | art/books/cars | 18 | 584 | 177 | 0.697 | 1.0 | 1.0 | 0.092 |
| ts-0210 | cooking/education/events | 18 | 575 | 179 | 0.689 | 0.8 | 0.8 | 0.071 |
| ts-0190 | philosophy/photography/podcasts | 18 | 548 | 179 | 0.673 | 0.8 | 0.8 | 0.107 |
| ts-0124 | books/cars/celebrities | 18 | 656 | 181 | 0.724 | 0.4 | 0.667 | 0.088 |
| ts-0025 | pets/philosophy/photography | 18 | 641 | 181 | 0.718 | 0.8 | 0.667 | 0.068 |
| ts-0086 | coding/cooking/education | 18 | 630 | 181 | 0.713 | 0.8 | 0.667 | 0.123 |
| ts-0175 | food/gaming/gardening | 18 | 630 | 181 | 0.713 | 0.8 | 0.667 | 0.104 |
| ts-0147 | news/pets/philosophy | 18 | 628 | 181 | 0.712 | 0.0 | 0.667 | 0.076 |
| ts-0120 | travel/weather/work | 18 | 615 | 181 | 0.706 | 1.0 | 0.667 | 0.1 |
| ts-0072 | science/shopping/social media | 18 | 611 | 181 | 0.704 | 0.8 | 0.667 | 0.064 |

## 10 worst (DESi shift-F1, then separation)

| traj | domains | turns | raw_tok | desi_tok | ratio | F1_A | F1_B | sep |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ts-0278 | shopping/social media/spirituality | 18 | 606 | 174 | 0.713 | 0.0 | 0.0 | -0.051 |
| ts-0005 | cooking/education/events | 18 | 589 | 174 | 0.705 | 0.0 | 0.0 | -0.028 |
| ts-0183 | languages/makeup/movies | 18 | 595 | 174 | 0.708 | 0.0 | 0.0 | -0.026 |
| ts-0090 | fashion/finance/fitness | 18 | 537 | 187 | 0.652 | 0.0 | 0.0 | -0.025 |
| ts-0104 | music/nature/news | 18 | 581 | 174 | 0.701 | 0.222 | 0.0 | -0.025 |
| ts-0256 | fitness/food/gaming | 18 | 556 | 174 | 0.687 | 0.0 | 0.0 | -0.023 |
| ts-0006 | education/events/fashion | 18 | 613 | 174 | 0.716 | 0.0 | 0.0 | -0.019 |
| ts-0203 | weather/work/art | 18 | 623 | 174 | 0.721 | 0.4 | 0.0 | -0.015 |
| ts-0204 | work/art/books | 18 | 606 | 174 | 0.713 | 0.25 | 0.0 | -0.01 |
| ts-0288 | books/cars/celebrities | 18 | 580 | 174 | 0.7 | 0.0 | 0.0 | -0.009 |

## DESi outperforms the raw-transcript proxy (F1_B > F1_A)

| traj | domains | turns | raw_tok | desi_tok | ratio | F1_A | F1_B | sep |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ts-0147 | news/pets/philosophy | 18 | 628 | 181 | 0.712 | 0.0 | 0.667 | 0.076 |
| ts-0146 | nature/news/pets | 18 | 630 | 185 | 0.706 | 0.0 | 0.5 | 0.069 |
| ts-0020 | makeup/movies/music | 18 | 538 | 187 | 0.652 | 0.0 | 0.444 | 0.062 |
| ts-0216 | food/gaming/gardening | 18 | 557 | 179 | 0.679 | 0.0 | 0.4 | 0.056 |
| ts-0093 | food/gaming/gardening | 18 | 654 | 181 | 0.723 | 0.0 | 0.333 | 0.082 |
| ts-0177 | gardening/health/history | 18 | 618 | 181 | 0.707 | 0.0 | 0.333 | 0.074 |
| ts-0232 | photography/podcasts/politics | 18 | 629 | 181 | 0.712 | 0.0 | 0.333 | 0.051 |
| ts-0242 | traditions/travel/weather | 18 | 544 | 183 | 0.664 | 0.0 | 0.286 | 0.038 |
| ts-0252 | education/events/fashion | 18 | 599 | 183 | 0.694 | 0.0 | 0.286 | 0.05 |
| ts-0287 | art/books/cars | 18 | 600 | 183 | 0.695 | 0.0 | 0.286 | 0.031 |

## DESi loses continuity (within-segment noisier than the shift)

| traj | domains | turns | raw_tok | desi_tok | ratio | F1_A | F1_B | sep |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ts-0004 | coding/cooking/education | 18 | 601 | 174 | 0.71 | 0.0 | 0.0 | -0.003 |
| ts-0005 | cooking/education/events | 18 | 589 | 174 | 0.705 | 0.0 | 0.0 | -0.028 |
| ts-0006 | education/events/fashion | 18 | 613 | 174 | 0.716 | 0.0 | 0.0 | -0.019 |
| ts-0062 | movies/music/nature | 18 | 576 | 174 | 0.698 | 0.25 | 0.0 | -0.001 |
| ts-0090 | fashion/finance/fitness | 18 | 537 | 187 | 0.652 | 0.0 | 0.0 | -0.025 |
| ts-0104 | music/nature/news | 18 | 581 | 174 | 0.701 | 0.222 | 0.0 | -0.025 |
| ts-0183 | languages/makeup/movies | 18 | 595 | 174 | 0.708 | 0.0 | 0.0 | -0.026 |
| ts-0203 | weather/work/art | 18 | 623 | 174 | 0.721 | 0.4 | 0.0 | -0.015 |
| ts-0204 | work/art/books | 18 | 606 | 174 | 0.713 | 0.25 | 0.0 | -0.01 |
| ts-0256 | fitness/food/gaming | 18 | 556 | 174 | 0.687 | 0.0 | 0.0 | -0.023 |

## Honesty
- Constructed shifts; deterministic lexical signals; no tuning.
