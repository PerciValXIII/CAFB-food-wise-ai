from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/presentations']
SERVICE_ACCOUNT_FILE = 'service_account.json'

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

slides_service = build('slides', 'v1', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)

def create_and_share_presentation(presentation_data):
    title = presentation_data.get('title', 'Untitled Presentation')
    
    # Step 1: Create the presentation
    presentation = slides_service.presentations().create(body={
        'title': title
    }).execute()
    presentation_id = presentation['presentationId']
    
    # Get the presentation to find the auto-created title slide
    presentation = slides_service.presentations().get(
        presentationId=presentation_id
    ).execute()
    
    # The first slide should be auto-created with the presentation
    if 'slides' in presentation and len(presentation['slides']) > 0:
        first_slide = presentation['slides'][0]
        
        # Find the title and subtitle placeholders on the first slide
        title_placeholder_id = None
        subtitle_placeholder_id = None
        
        for element in first_slide.get('pageElements', []):
            if 'shape' in element and 'placeholder' in element['shape']:
                placeholder_type = element['shape']['placeholder']['type']
                if placeholder_type == 'TITLE' or placeholder_type == 'CENTERED_TITLE':
                    title_placeholder_id = element['objectId']
                elif placeholder_type == 'SUBTITLE':
                    subtitle_placeholder_id = element['objectId']
        
        # Create a list of requests to update the first slide
        first_slide_requests = []
        
        # Update the title if found
        if title_placeholder_id:
            first_slide_requests.append({
                'insertText': {
                    'objectId': title_placeholder_id,
                    'insertionIndex': 0,
                    'text': title
                }
            })
            
            # Format the title text (larger font, bold, center-aligned)
            first_slide_requests.append({
                'updateTextStyle': {
                    'objectId': title_placeholder_id,
                    'style': {
                        'fontFamily': 'Arial',
                        'fontSize': {
                            'magnitude': 36,
                            'unit': 'PT'
                        },
                        'bold': True,
                    },
                    'textRange': {
                        'type': 'ALL'
                    },
                    'fields': 'fontFamily,fontSize,bold'
                }
            })
            
            # Center align the title text
            first_slide_requests.append({
                'updateParagraphStyle': {
                    'objectId': title_placeholder_id,
                    'style': {
                        'alignment': 'CENTER'
                    },
                    'textRange': {
                        'type': 'ALL'
                    },
                    'fields': 'alignment'
                }
            })
        
        # Delete the subtitle placeholder entirely if found
        if subtitle_placeholder_id:
            first_slide_requests.append({
                'deleteObject': {
                    'objectId': subtitle_placeholder_id
                }
            })
        
        # Execute the updates for the first slide
        if first_slide_requests:
            slides_service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': first_slide_requests}
            ).execute()
    
    # Step 3: Add content slides with improved formatting
    slide_keys = sorted([key for key in presentation_data.keys() if key.startswith("Slide")])
    slides_dict = {}
    for key in slide_keys:
        prefix = key.split("_")[0]
        if prefix not in slides_dict:
            slides_dict[prefix] = {}
        if "_Heading" in key:
            slides_dict[prefix]["heading"] = presentation_data[key]
        elif "_Content" in key:
            slides_dict[prefix]["content"] = presentation_data[key]

    for slide in sorted(slides_dict.keys()):
        heading = slides_dict[slide].get("heading", "")
        content = slides_dict[slide].get("content", "")
        
        # Create the content slide
        create_slide_request = {
            'createSlide': {
                'slideLayoutReference': {
                    'predefinedLayout': 'TITLE_AND_BODY'
                }
            }
        }
        
        response = slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': [create_slide_request]}
        ).execute()
        
        slide_id = response['replies'][0]['createSlide']['objectId']
        
        # Get the updated presentation to find the created slide elements
        presentation = slides_service.presentations().get(
            presentationId=presentation_id
        ).execute()
        
        slide_obj = next(s for s in presentation['slides'] if s['objectId'] == slide_id)
        
        # Find title and body placeholders
        title_id = None
        body_id = None
        
        for element in slide_obj.get('pageElements', []):
            if 'shape' in element and 'placeholder' in element['shape']:
                placeholder_type = element['shape']['placeholder']['type']
                if placeholder_type == 'TITLE':
                    title_id = element['objectId']
                elif placeholder_type == 'BODY':
                    body_id = element['objectId']
        
        # Add text to the placeholders
        text_requests = []
        
        if title_id:
            text_requests.append({
                'insertText': {
                    'objectId': title_id,
                    'insertionIndex': 0,
                    'text': heading
                }
            })
            
            # Format the heading (apply better font, size and center-align)
            text_requests.append({
                'updateTextStyle': {
                    'objectId': title_id,
                    'style': {
                        'fontFamily': 'Arial',
                        'fontSize': {
                            'magnitude': 28,
                            'unit': 'PT'
                        },
                        'bold': True,
                        'foregroundColor': {
                            'opaqueColor': {
                                'rgbColor': {
                                    'red': 0.2,
                                    'green': 0.2,
                                    'blue': 0.6
                                }
                            }
                        }
                    },
                    'textRange': {
                        'type': 'ALL'
                    },
                    'fields': 'fontFamily,fontSize,bold,foregroundColor'
                }
            })
            
            # Center align the heading
            text_requests.append({
                'updateParagraphStyle': {
                    'objectId': title_id,
                    'style': {
                        'alignment': 'CENTER'
                    },
                    'textRange': {
                        'type': 'ALL'
                    },
                    'fields': 'alignment'
                }
            })
            
        if body_id:
            text_requests.append({
                'insertText': {
                    'objectId': body_id,
                    'insertionIndex': 0,
                    'text': content
                }
            })
            
            # Format the body text (clean font, appropriate size, left-aligned)
            text_requests.append({
                'updateTextStyle': {
                    'objectId': body_id,
                    'style': {
                        'fontFamily': 'Arial',
                        'fontSize': {
                            'magnitude': 18,
                            'unit': 'PT'
                        }
                    },
                    'textRange': {
                        'type': 'ALL'
                    },
                    'fields': 'fontFamily,fontSize'
                }
            })
            
            # Left align the body text and add some spacing
            text_requests.append({
                'updateParagraphStyle': {
                    'objectId': body_id,
                    'style': {
                        'alignment': 'START',
                        'lineSpacing': 125,  # 1.25x line spacing for better readability
                        'spaceAbove': {
                            'magnitude': 8,
                            'unit': 'PT'
                        },
                        'spaceBelow': {
                            'magnitude': 8,
                            'unit': 'PT'
                        }
                    },
                    'textRange': {
                        'type': 'ALL'
                    },
                    'fields': 'alignment,lineSpacing,spaceAbove,spaceBelow'
                }
            })
            
        if text_requests:
            slides_service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': text_requests}
            ).execute()

    # Step 4: Add a background color to all slides
    slides = slides_service.presentations().get(
        presentationId=presentation_id
    ).execute().get('slides', [])
    
    background_requests = []
    for slide_obj in slides:
        slide_id = slide_obj['objectId']
        background_requests.append({
            'updatePageProperties': {
                'objectId': slide_id,
                'pageProperties': {
                    'pageBackgroundFill': {
                        'solidFill': {
                            'color': {
                                'rgbColor': {
                                    'red': 0.95,
                                    'green': 0.95,
                                    'blue': 1.0
                                }
                            }
                        }
                    }
                },
                'fields': 'pageBackgroundFill.solidFill.color'
            }
        })
    
    if background_requests:
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': background_requests}
        ).execute()

    # Step 5: Make it public
    drive_service.permissions().create(
        fileId=presentation_id,
        body={
            'role': 'writer',
            'type': 'anyone'
        }
    ).execute()

    return f"https://docs.google.com/presentation/d/{presentation_id}/edit"

# # Example usage
# presentation_data = {
#     "title": "Professional Presentation",
#     "Slide1_Heading": "Introduction",
#     "Slide1_Content": "• This presentation showcases our key findings\n• Created with Google Slides API\n• Professionally formatted with custom styling",
#     "Slide2_Heading": "Key Points",
#     "Slide2_Content": "1. Improved visual aesthetics\n2. Consistent formatting across slides\n3. Professional color scheme\n4. Better readability with appropriate font sizes"
# }

# link = create_and_share_presentation(presentation_data)
# print("✅ Public Google Slides link:", link)