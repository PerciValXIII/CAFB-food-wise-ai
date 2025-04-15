from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
SERVICE_ACCOUNT_FILE = 'service_account.json'

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

docs_service = build('docs', 'v1', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)

def create_and_share_document(document_data):
    title = document_data.get('title', 'Untitled Document')
    
    # Step 1: Create the document
    document = docs_service.documents().create(body={
        'title': title
    }).execute()
    document_id = document['documentId']
    
    # Step 2: Prepare requests for formatting and content
    requests = []
    
    # Set page margins (1 inch on all sides)
    requests.append({
        'updateDocumentStyle': {
            'documentStyle': {
                'marginTop': {
                    'magnitude': 72,
                    'unit': 'PT'
                },
                'marginBottom': {
                    'magnitude': 72,
                    'unit': 'PT'
                },
                'marginLeft': {
                    'magnitude': 72,
                    'unit': 'PT'
                },
                'marginRight': {
                    'magnitude': 72,
                    'unit': 'PT'
                }
            },
            'fields': 'marginTop,marginBottom,marginLeft,marginRight'
        }
    })

    # Add title
    requests.append({
        'insertText': {
            'location': {
                'index': 1
            },
            'text': title + '\n\n'
        }
    })
    
    # Format title - FIXED: using weightedFontFamily instead of fontFamily
    requests.append({
        'updateTextStyle': {
            'range': {
                'startIndex': 1,
                'endIndex': 1 + len(title)
            },
            'textStyle': {
                'fontSize': {
                    'magnitude': 24,
                    'unit': 'PT'
                },
                'bold': True,
                'foregroundColor': {
                    'color': {
                        'rgbColor': {
                            'red': 0.2,
                            'green': 0.2,
                            'blue': 0.6
                        }
                    }
                },
                'weightedFontFamily': {
                    'fontFamily': 'Arial'
                }
            },
            'fields': 'fontSize,bold,foregroundColor,weightedFontFamily'
        }
    })
    
    # Center align the title
    requests.append({
        'updateParagraphStyle': {
            'range': {
                'startIndex': 1,
                'endIndex': 1 + len(title) + 1  # Include the newline
            },
            'paragraphStyle': {
                'alignment': 'CENTER',
                'spaceBelow': {
                    'magnitude': 20,
                    'unit': 'PT'
                }
            },
            'fields': 'alignment,spaceBelow'
        }
    })
    
    # Current position in the document
    current_index = 1 + len(title) + 2  # Title + two newlines
    
    # Process subheadings and content
    subheading_keys = sorted([key for key in document_data.keys() if key.startswith("Subheading")])
    
    for key in subheading_keys:
        subheading_number = key[10:]  # Extract number from "Subheading1", "Subheading2", etc.
        content_key = "Content" + subheading_number
        
        subheading = document_data.get(key, "")
        content = document_data.get(content_key, "")
        
        # Add subheading
        requests.append({
            'insertText': {
                'location': {
                    'index': current_index
                },
                'text': subheading + '\n'
            }
        })
        
        # Format subheading - FIXED: using weightedFontFamily
        requests.append({
            'updateTextStyle': {
                'range': {
                    'startIndex': current_index,
                    'endIndex': current_index + len(subheading)
                },
                'textStyle': {
                    'fontSize': {
                        'magnitude': 16,
                        'unit': 'PT'
                    },
                    'bold': True,
                    'foregroundColor': {
                        'color': {
                            'rgbColor': {
                                'red': 0.2,
                                'green': 0.2,
                                'blue': 0.6
                            }
                        }
                    },
                    'weightedFontFamily': {
                        'fontFamily': 'Arial'
                    }
                },
                'fields': 'fontSize,bold,foregroundColor,weightedFontFamily'
            }
        })
        
        # Style subheading paragraph
        requests.append({
            'updateParagraphStyle': {
                'range': {
                    'startIndex': current_index,
                    'endIndex': current_index + len(subheading) + 1  # Include newline
                },
                'paragraphStyle': {
                    'spaceAbove': {
                        'magnitude': 18,
                        'unit': 'PT'
                    },
                    'spaceBelow': {
                        'magnitude': 8,
                        'unit': 'PT'
                    }
                },
                'fields': 'spaceAbove,spaceBelow'
            }
        })
        
        current_index += len(subheading) + 1  # Subheading + newline
        
        # Add content paragraph
        requests.append({
            'insertText': {
                'location': {
                    'index': current_index
                },
                'text': content + '\n\n'  # Add extra newline after paragraph
            }
        })
        
        # Format content paragraph text - FIXED: using weightedFontFamily
        requests.append({
            'updateTextStyle': {
                'range': {
                    'startIndex': current_index,
                    'endIndex': current_index + len(content)
                },
                'textStyle': {
                    'fontSize': {
                        'magnitude': 11,
                        'unit': 'PT'
                    },
                    'weightedFontFamily': {
                        'fontFamily': 'Arial'
                    }
                },
                'fields': 'fontSize,weightedFontFamily'
            }
        })
        
        # Style content paragraph
        requests.append({
            'updateParagraphStyle': {
                'range': {
                    'startIndex': current_index,
                    'endIndex': current_index + len(content) + 2  # Include double newline
                },
                'paragraphStyle': {
                    'lineSpacing': 115,  # 1.15x line spacing
                    'spaceBelow': {
                        'magnitude': 10,
                        'unit': 'PT'
                    }
                },
                'fields': 'lineSpacing,spaceBelow'
            }
        })
        
        current_index += len(content) + 2  # Content + double newline
    
    # Execute all the formatting requests
    docs_service.documents().batchUpdate(
        documentId=document_id,
        body={'requests': requests}
    ).execute()
    
    # Make it public with write permissions
    drive_service.permissions().create(
        fileId=document_id,
        body={
            'role': 'writer',
            'type': 'anyone'
        }
    ).execute()
    
    return f"https://docs.google.com/document/d/{document_id}/edit"

# Example usage with the provided JSON data
# document_data = {
#     "title": "Enhancing Food Security in Business: A Strategic Necessity",
#     "Subheading1": "Understanding the Impact of Food Insecurity",
#     "Content1": "Food insecurity is a pressing issue that significantly undermines the health, education, and productivity of communities. It is especially concerning for children, as illustrated by the alarming statistic that one in five children in the U.S. lives in a food-insecure household. In Washington, D.C., these numbers are even more striking, with one in three children affected. This pervasive issue not only impacts individual well-being but also stymies economic growth and development. Businesses that invest in combating hunger can thus play a pivotal role in fostering healthier communities and facilitating economic prosperity.",
#     "Subheading2": "Corporate Commitment to Hunger Solutions",
#     "Content2": "Businesses like Safeway and Giant Food have taken significant steps to address food insecurity. As part of the hunger action month initiatives, Safeway has been actively engaging in conversations with other businesses to develop localized hunger solutions in Washington, D.C. Meanwhile, Giant Food has been collaborating with the Capital Area Food Bank to provide practical solutions, such as offering recipes that make fresh food more accessible and manageable for low-income families.",
#     "Subheading3": "Leveraging Disruptions in the Private Sector",
#     "Content3": "Recent disruptions in the private sector present businesses with opportunities to address food insecurity innovatively. The acquisition of Whole Foods by Amazon and the divestment of Nestle's candy division in favor of healthier options are examples of how market shifts can open new avenues for delivering nutritious food. Businesses can capitalize on the rising demand for healthier food to create better access models, particularly in food deserts and low-income urban areas.",
#     "Subheading4": "The Role of NGOs and Food Banks",
#     "Content4": "Organizations and NGOs are critical players in tackling food security, often collaborating with corporations to widen food access. The Capital Area Food Bank, for example, increases the distribution of healthy foods like fruits and vegetables in partnership with private sector companies. They also work to influence consumer behavior by demonstrating the demand for healthy produce, which can encourage retailers to expand market reach in underserved areas.",
#     "Subheading5": "FAO's Global Mandate in Enhancing Food Security",
#     "Content5": "On a global scale, the Food and Agricultural Organization (FAO) plays a crucial role in addressing food insecurity by providing vital data and early warnings related to food production and consumption. The FAO's efforts are geared toward improving agricultural productivity and reducing global hunger. Their abilities to promote cross-border agreements and share expertise are indispensable in supporting developing countries to achieve food security.",
#     "Subheading6": "Future Directions and Collaborative Efforts",
#     "Content6": "As our global food ecosystem evolves, the need for inclusive food security measures becomes even more pressing. Collaborative efforts between businesses, NGOs, and international organizations can initiate meaningful change. By recognizing the market opportunities and responsibilities that arise from private sector disruptions, and capitalizing on the collective use of resources and expertise, stakeholders can ensure a more equitable food supply benefiting all economic strata."
# }

# link = create_and_share_document(document_data)
# print("✅ Public Google Docs link:", link)