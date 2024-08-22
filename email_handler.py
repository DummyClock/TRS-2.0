import os, smtplib, time
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#from auth import TRAINER_GMAIL, TRAINER_GMAIL_PASSWORD
TRAINER_GMAIL = os.environ['TRAINER_GMAIL']
TRAINER_GMAIL_PASSWORD = os.environ['TRAINER_GMAIL_PASSWORD']

def sendHTMLEmail(row_of_trainer_data, row_of_headers, receiver, lang):
    #Prepare HTML report
    html = buildHTMLPart(row_of_trainer_data, row_of_headers)

    #Prepare email credentials
    smtpObj = smtplib.SMTP()
    sender = TRAINER_GMAIL
    message = MIMEMultipart("Alternative")
    subject = "Training Report for [" +  row_of_trainer_data[row_of_headers.index("Position")] +"] | Chick-Fil-A"
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receiver

    #Attatch HTML text
    if lang != 'en':
      html = translateHTML(html, lang)
    html_msg = MIMEText(html, 'html')
    message.attach(html_msg)

    # Send the email
    try:
      api_error = True
      api_error_counter = 3
      with smtplib.SMTP("smtp.gmail.com", 587) as server:
          api_error = False
          server.starttls()  # Secure the connection
          server.login(TRAINER_GMAIL, TRAINER_GMAIL_PASSWORD)
          server.send_message(message)
          server.quit
    except (smtplib.SMTPConnectError, smtplib.SMTPConnectError):
     api_error = apiTimeOut(api_error_counter)
     api_error_counter -= 1
    except smtplib.SMTPRecipientsRefused:
       print("Invalid recipent email proccessed")

    return "email sent"

def translateHTML(html, transTo):
  soup = BeautifulSoup(html, 'html5lib')
  translator = GoogleTranslator(source='en', target=transTo)
  textNodes = []

  #Get text nodes
  for node in soup.find_all(string=True):
    text = node.get_text()
    if "\n" in text:
       continue
    textNodes.append(text)
  translations = [translator.translate(text) for text in textNodes]

  #Replace html's text elements
  i = 0
  for node in soup.find_all(string=True):
    if "\n" in node.get_text():
      continue
    node.string.replace_with(translations[i])
    i += 1

  return str(soup)

def buildHTMLPart(header_data, training_data):
    warning = "This an automated message. If you have any questions regarding your report, please refer to a lead or trainer. Likewise, if you're confused about your report or want advice, please refer to a lead or trainer. <br><br>"
    pos = header_data[training_data.index("Position")]
    trainee = header_data[training_data.index("Trainee")]
    trainer = header_data[training_data.index("Trainer")]
    summ =  header_data[training_data.index("Shift Summary")]
    html_part1 = """
    <!DOCTYPE html>
    <html lang='en-US'>
        <head>
            <style>
                table, th, td {border: 1px solid black; border-collapse: collapse; } th, td {padding: 5px; text-align: left;} td {width: 200px; text-align: right} 
            </style><img src='https://1000logos.net/wp-content/uploads/2021/04/Chick-fil-A-logo-500x281.png' alt='Chic-Fil-A> class="center"'
        </head>
        <body>
            <h5 style="color:gray">Warning: Do not reply to email!<br>""" + warning + """</h5>
            <h1 align="left">""" + pos + """ Training Report</h1>
            <h3 align="left">What is this?</h3>
            <h5 align="left">This email contains a report documenting your performance training on """ + pos + """. Below you will find details on your performance; this report is designed to help you notice your strengths and weakness. </h5>
                    <ul align="left">
                        <li>If you're seeking tips or advice to improve be sure to ask any trainer or lead; they will be more than happy to assist you!</li>
                        <li style="color:gray">Alternatively, you may also reference the <u>Pathways Modules</u> listed at the bottom. :)</li>
                    </ul>
            <br>
            <h2 align="left">Report Details</h2>
                <ul align="left">
                    <li>Trainer: """ + trainer + """</li>
                    <li>Pupil: """ + trainee + """</li>
                </ul><br>
                <table>
                    <tr>
                        <th>
                            <div>Details</div>
                        </th>
                        <td>
                            <div>Info</div>
                        </td>
                    </tr>
    """

    # Build the data table
    body1 = ""
    for index in range(len(header_data)):
        body1 = body1 + "<tr><th>" + str(training_data[index]) + "</th><td>" + str(header_data[index]) + "</td></tr>"
    body1 = body1 + "</table></body><br><footer>"     #close table

    html_part2 = """
                <h2 id='pathways_section'>Pathways Training Resources</h2><h3>What is this?</h3>
                <p>Below are links to official Chic-Fil-A training resources. If you're looking for specific details regarding this position, these are the pages you should check! Feel free to use them as an additional reference! :)</p>
                <p>Can't login? Ask a director to help retrieve your username or password. If you're unsure who is a director, ask your shift lead to help direct you towards them.</p>
                <br><h3>Pathways Links</h3>
                <div class='button-collection' align="center">""" + getPathwaysButtons(pos) + """</div>
                <br><br><br>
                <h5>Thank you for taking the time to review your report. I deeply value your commitment! At Chic-Fil-A quality is vital to our operations, thus we want to provide resources to our employees that'll help us to continue providing quality products to our guests! So, thank you for your participation in our mission! Remember, practice makes perfect; you may not be great at everything right away. However, with enough time and proper effort you'll be able to get to wherever you want to be, both with us and with anything in your life!</h5>
            </footer>
        </html>
    """

    return html_part1 + body1 + html_part2

def getPathwaysButtons(position):
    img = 'https://play-lh.googleusercontent.com/6CrgwWaEPe0J6e8RrS98b3StD3pD0zpQ6jpxMZEpkUCtbFYOpvk7riwoIxJYWq9j3D9c=w240-h480'
    divHeader = "<div class='row' style='display:flex; flex-direcction: row;justify-content: center;alight-items:center'><style>.row{padding-left: 15px; padding-right:15px;} .button{padding: 20px;} .text-section{width: 170px; word-wrap: break-word;} div {text-align:center;}</style>";
    buttons = divHeader

    
    if position == "Breading":
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/cf44e9e7-182a-405a-949c-3829c47dd822','1) Ice Bath Breading Table: Maintaining and Cleaning',img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/761ac446-ccb2-451f-bb4c-812a67d86915', '2) Breading and Loading Filets', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/21c0df6f-55de-4f8e-9895-be18c729e03a', '3) Breading Nuggets', img)
      
      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/d58eb1b1-fa13-4c51-bed1-39b7ee52c742', '4) Breading Chick-n-Strips™', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/b8c33556-e602-47eb-8bf2-a9a2a1276d1b','5) Loading Grilled Chicken',img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/430e29d3-e2c1-4a8e-80b3-c82b26640b9e','6) Handling Raw Chicken Safely',img)

      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/bb4f69be-8e38-4d16-a82a-e85d62425d33','7) Handling Sealed Bags of Chicken',img)
      buttons = buttons + "</div>"
    elif position ==  "Buns":
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/4034b22d-dd29-4ed1-b4db-b82f4be4c4dd', "1) Thawing and Toasting Buns", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/b4cd03cf-3775-4f62-9fa8-6f464c92916f', '2) Serving Chicken Noodle Soup', img)
      buttons = buttons + "</div>"
    elif position ==  "Dish":
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/faeb5c20-3a18-4cb2-a8b0-d589b3a2da0d', "1) Washing Dishes by Hand", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/3a4b5cae-f265-44be-9bec-00744b3786b0', "2) Cleaning Sinks: Compartment Sinks", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/dee16f32-4d85-4d5d-a758-e6f00aee6756', "3) High Temp Dishwasher: Essential Information", img)

      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/ac441177-a965-4b19-804c-3da1a5c1c4bc', "4) High Temp Dishwasher: Washing Dishes", img)
      buttons = buttons + '</div>'
    elif position ==  "Fries":
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/9c63c61e-b550-4e21-9d2c-54464c25d0eb', "1) Preparing Waffle Fries", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/8a5e8e21-8a8e-4601-aec5-c18a1ffea013', "2) Waffle Fry Carton Dispenser", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/22ba951e-a977-4b6c-bfde-42a4750c8ffe', "3) Fry Warming Station: Essential Information", img)

      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/237b25ff-5b29-4cf8-b0d6-58bd6baad6e9', "4) Fry Warming Station: Essential Information", img)      
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/f82d83ee-9894-4149-8532-2f6fcb134a6d', "5) Potato Fryer: Essential Information", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/f9497106-d4d2-4513-9ebc-69a093423d9d', "6) Skimming Canola Oil Frequently", img)
      buttons = buttons + "</div>"
    elif position ==  "Machines":
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/3d238d29-ee65-4663-b45c-0935d9e96560', '1) Cooking Chick-fil-A® or Spicy Filets', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/c5d11924-5c1e-4bac-bc56-a6bacc22d84f', '2) Cooking Nuggets', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/9549b56e-1da1-43a0-a0d8-017ae9320012', '3) Cooking Chick-n-Strips', img)

      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/f9022ca5-4cea-494a-adc9-5996d9b428c6', '4) Cooking Grilled Chicken', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/1e485c15-3606-4425-ba28-cf62a86398b2', '5) Chicken Transfer Station', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/f82d83ee-9894-4149-8532-2f6fcb134a6d', "6) Maintaining Oil in Fryers", img)

      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/c659a3f6-39f0-4e5a-8126-c371b9255377', '7) Hybrid Chicken Fryer: Essential Information', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/916caa8e-a2f3-452b-9b35-dd8b5c68ed6a', '8) Hybrid Chicken Fryer: Express Clean', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/4c868397-354b-4020-bc13-7149df46aa19', '9) Hybrid Chicken Fryer: Switching Chicken Fryer Mode', img)

      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/13163c93-c526-490a-9215-a576f3e73190', '10) Garland Grill 2.0: Essential Information', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/4360de45-a40b-4b4e-9d3a-eb23a1221bad', '11) Garland Grill 2.0: Cleaning Throughout Day', img)
      buttons = buttons + "</div>"
    elif position ==  "Rotations":
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/aa2dc819-3e56-4ce4-af02-77599448f912', '1) Lean Thawing and Fileting Overview', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/53a139b1-5115-4acf-853e-cc86b0f883e2', '2) Raw Chicken Control Label Information', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/2d5b2ce0-6ab7-4cf5-a7fa-341a76202e3c', '3) Lean Chicken Thawing', img)

      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/5a04498f-7042-47f9-8508-3b6998084bfd', '4) Fileting Using Filet Roller', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/757410c2-244a-4bcd-9833-7a89f5afa6fb', '5) Marinating Grilled Filets', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/f1fb21db-b378-4f36-b600-c50eeef52a21', '6) Draining and Marinating Grilled Nuggets', img)

      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/2509ff95-9667-4c92-822d-9d954086dca2', '7) Chicken Quick Thaw', img)

      buttons = buttons + "</div>"
    elif position ==  "Screens":
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/46c72fc0-e5e2-412c-be2d-b9d131bb1741', "1) Boxing Chick-n-Strips™ and Nuggets", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/6f50da48-b030-44a0-b9e3-cd4c7f849ae1', "2) Assembling and Holding Chick‑fil‑A® Chicken Sandwiches and Spicy Chicken Sandwiches", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/99d12b0f-e973-4a8e-89c7-ef17552ef666', "3) Holding Cooked Breaded Chicken", img)      

      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/e216d35c-d7ff-4b80-80d7-20bfed1dd3ce', "4) Lean Chicken Entrées (LCE) Overview", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/0064e197-2d41-4046-9907-7041b48e17d6', "5) Automated Holding Assistant (AHA)", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/581d36b4-fcc6-44e1-888f-903636acc73d', "Bonus: Centerline 2.0", img)

      buttons = buttons + "</div>"
    elif position ==  "Set-Ups":
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/6f50da48-b030-44a0-b9e3-cd4c7f849ae1', "1) Assembling and Holding Chick‑fil‑A® Chicken Sandwiches and Spicy Chicken Sandwiches", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/08e9776c-126a-4bf1-bfb9-36fc1c9aa021', "2) Assembling Deluxe Sandwiches", img)
      buttons = buttons + generateHTMLButton("https://www.pathway.cfahome.com/doc/6075cfab-51af-48ee-a8d2-3adc926d56f7", "3) Assembling Grilled Chicken and Club Sandwiches", img)

      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/1dbe8cad-8915-4f8c-ad1a-00e240db282a', '4) Customization: Lettuce Wrap Sandwich', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/57127409-f1db-43e0-9686-669b21d4c5d5', "5) Packaging Grilled Nuggets", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/705687e4-965b-46b5-9184-24201b5ae605', "6) Slicing Hot Nuggets onto Salads", img)

      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/705687e4-965b-46b5-9184-24201b5ae605', "7) Cupping and Holding Mac & Cheese", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/b4cd03cf-3775-4f62-9fa8-6f464c92916f', '8) Serving Chicken Noodle Soup', img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/e216d35c-d7ff-4b80-80d7-20bfed1dd3ce', "9) Lean Chicken Entrées (LCE) Overview", img)

      buttons = buttons + "</div>" + divHeader
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/0064e197-2d41-4046-9907-7041b48e17d6', "10) Automated Holding Assistant (AHA)", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/99d12b0f-e973-4a8e-89c7-ef17552ef666', "11) Holding Cooked Breaded Chicken", img)
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/doc/581d36b4-fcc6-44e1-888f-903636acc73d', "Bonus: Centerline 2.0", img)
      buttons = buttons + "</div>"
    else:
      buttons = buttons + generateHTMLButton('https://www.pathway.cfahome.com/', "Pathways Home Page", img) + "</div>"
  
    return buttons

def generateHTMLButton(link, text, img):

    return  "<div class='button'><div class='img-section'><a href=" +link +"><img src='"+ img + "' alt='Training Module' width=100px></a></div><div class='text-section'><a style='text-decoration:none' href="+ link + "><div><h4>"+text+"</h4></div></a></div></div>"

def apiTimeOut(api_error_counter):
