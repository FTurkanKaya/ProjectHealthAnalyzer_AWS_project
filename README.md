# ProjectHealthAnalyzer

**ProjectHealthAnalyzer** is een cloud-gebaseerd project dat de gezondheid en activiteit van softwareprojecten op GitHub analyseert. Het combineert data engineering, serverless computing en analytics om inzicht te geven in repositories en hun ontwikkeling.

---

## 🔹 Doelen

- Automatisch gegevens verzamelen van GitHub repositories
- Data opslaan en beheren in AWS S3
- Analyse en rapportage van project metrics zoals sterren, forks en issues
- Serverless architectuur gebruiken met AWS Lambda
- Portfolio demonstratie van cloud en data vaardigheden

---

## 🔹 Functionaliteiten

- Data ophalen van één of meerdere GitHub repositories
- S3 opslag van de verkregen JSON data
- Berekenen van eenvoudige "Project Health Score" gebaseerd op metrics
- Optioneel: visualisatie en analyse via AWS Athena of QuickSight
- Automatische uitvoering mogelijk via CloudWatch Events

---

## 🔹 Uit te voeren stappen (kort overzicht)

1. GitHub Token aanmaken voor API toegang
2. AWS S3 bucket aanmaken voor opslag
3. Lambda functie opzetten met environment variables:
   - GitHub token
   - Bucket naam
   - Bestandsvoorvoegsel
4. Lambda code implementeren en testen
5. IAM permissies configureren voor Lambda om naar S3 te schrijven
6. (Optioneel) Meerdere repositories monitoren en health score berekenen
7. (Optioneel) Automatisering via CloudWatch Events

---

## 🔹 Resultaat

- JSON bestanden in S3 met repository informatie
- Mogelijkheid om metrics te analyseren en project health te visualiseren
- Eenvoudig uitbreidbaar voor meerdere projecten

