from functools import reduce

__first_table_color = {
    'red': 184 / 255,
    'green': 204 / 255,
    'blue': 228 / 255,
}
__second_table_color = {
    'red': 219 / 255,
    'green': 229 / 255,
    'blue': 241 / 255,
}

__earning_header_color = {
    'red': 155 / 255,
    'green': 187 / 255,
    'blue': 89 / 255
}
__expense_header_color = {
    'red': 192 / 255,
    'green': 80 / 255,
    'blue': 77 / 255
}
__summary_header_color = {
    'red': 247 / 255,
    'green': 150 / 255,
    'blue': 70 / 255
}


def get_sheet_format(sheet_id):
    start_column = 0
    end_columns = {4: __earning_header_color, 8: __expense_header_color, 11: __summary_header_color}
    table_format = []
    for col, header in end_columns.items():
        table_format.append({
            'addBanding': {
                'bandedRange': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 1,
                        'endRowIndex': 35,
                        'startColumnIndex': start_column,
                        'endColumnIndex': col,
                    },
                    'rowProperties': {
                        'headerColor': header,
                        'firstBandColor': __first_table_color,
                        'secondBandColor': __second_table_color
                    },
                },
            }
        })
        start_column = col

    start_columns = [3, 7]
    invisible_cells = list(map(lambda inv_col: {
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'COLUMNS',
                'startIndex': inv_col,
                'endIndex': inv_col + 1,
            },
            'properties': {
                'pixelSize': 1
            },
            'fields': '*'
        }
    }, start_columns))

    start_columns = [0, 4]
    elements_cell = reduce(lambda acc, elem_col: acc + [{
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'COLUMNS',
                'startIndex': elem_col,
                'endIndex': elem_col + 1,
            },
            'properties': {
                'pixelSize': 80
            },
            'fields': '*'
        }
    }, {
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'COLUMNS',
                'startIndex': elem_col + 1,
                'endIndex': elem_col + 3,
            },
            'properties': {
                'pixelSize': 150
            },
            'fields': '*'
        }
    }, {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 2,
                "startColumnIndex": elem_col,
                "endColumnIndex": elem_col + 1,
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "DATE",
                        "pattern": "dd-mmm"
                    },
                    "horizontalAlignment": 'CENTER',
                    "verticalAlignment": 'MIDDLE',
                }
            },
            "fields": "*"
        }
    },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 2,
                    "startColumnIndex": elem_col + 1,
                    "endColumnIndex": elem_col + 2,
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": 'CENTER',
                        "verticalAlignment": 'MIDDLE',
                    }
                },
                "fields": "*"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 2,
                    "startColumnIndex": elem_col + 2,
                    "endColumnIndex": elem_col + 3,
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {
                            "type": "CURRENCY"
                        },
                        "horizontalAlignment": 'CENTER',
                        "verticalAlignment": 'MIDDLE',
                    }
                },
                "fields": "*"
            }
        }], start_columns, [])

    __sheet_format = table_format + invisible_cells + elements_cell + [
        # Summary formats
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 2,
                    "endRowIndex": 3,
                    "startColumnIndex": 8,
                    "endColumnIndex": 9,
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {
                            "type": "CURRENCY"
                        },
                        "horizontalAlignment": 'CENTER',
                        "verticalAlignment": 'MIDDLE',
                    },
                    "userEnteredValue": {
                        "formulaValue": "=(SUM(C3:C))-SUM(G3:G)"
                    }

                },
                "fields": "*"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 2,
                    "endRowIndex": 3,
                    "startColumnIndex": 9,
                    "endColumnIndex": 10,
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {
                            "type": "CURRENCY"
                        },
                        "horizontalAlignment": 'CENTER',
                        "verticalAlignment": 'MIDDLE',
                    },
                    "userEnteredValue": {
                        "formulaValue": "=SUM(C3:C)"
                    }

                },
                "fields": "*"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 2,
                    "endRowIndex": 3,
                    "startColumnIndex": 10,
                    "endColumnIndex": 11,
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {
                            "type": "CURRENCY"
                        },
                        "horizontalAlignment": 'CENTER',
                        "verticalAlignment": 'MIDDLE',
                    },
                    "userEnteredValue": {
                        "formulaValue": "=SUM(G3:G)"
                    }

                },
                "fields": "*"
            }
        },
        {
            'updateDimensionProperties': {
                'range': {
                    'sheetId': sheet_id,
                    'dimension': 'ROWS',
                    'startIndex': 1,
                    'endIndex': 2,
                },
                'properties': {
                    'pixelSize': 26
                },
                'fields': '*'
            }
        },
        {
            "addChart": {
                "chart": {
                    "spec": {
                        "title": "Month Expenses",
                        "hiddenDimensionStrategy": 'SHOW_ALL',
                        "pieChart": {
                            "legendPosition": 'LABELED_LEGEND',
                            "domain": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": sheet_id,
                                        "startRowIndex": 2,
                                        "startColumnIndex": 5,
                                        "endColumnIndex": 6
                                    }]
                                }
                            },
                            "series": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": sheet_id,
                                        "startRowIndex": 2,
                                        "startColumnIndex": 6,
                                        "endColumnIndex": 7
                                    }]
                                }
                            }
                        }
                    },
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {"sheetId": sheet_id, "rowIndex": 1, "columnIndex": 12},
                            "widthPixels": 730,
                            "heightPixels": 635
                        }
                    }
                }
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet_id,
                        "startRowIndex": 2,
                        "endRowIndex": 3,
                        "startColumnIndex": 8,
                        "endColumnIndex": 9
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": 'NUMBER_GREATER',
                            "values": [
                                {
                                    "userEnteredValue": "0"
                                }
                            ]
                        },
                        "format": {
                            "backgroundColor": __earning_header_color
                        }
                    }
                }
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet_id,
                        "startRowIndex": 2,
                        "endRowIndex": 3,
                        "startColumnIndex": 8,
                        "endColumnIndex": 9
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": 'NUMBER_LESS_THAN_EQ',
                            "values": [
                                {
                                    "userEnteredValue": "0"
                                }
                            ]
                        },
                        "format": {
                            "backgroundColor": __expense_header_color
                        }
                    }
                }
            }
        }
    ]
    return __sheet_format


table_titles = [
    {"userEnteredValue": {"stringValue": "Date"},
     "userEnteredFormat": {"horizontalAlignment": 'CENTER', "verticalAlignment": 'MIDDLE'}},
    {"userEnteredValue": {"stringValue": "Description"},
     "userEnteredFormat": {"horizontalAlignment": 'CENTER', "verticalAlignment": 'MIDDLE'}},
    {"userEnteredValue": {"stringValue": "Earnings"},
     "userEnteredFormat": {"horizontalAlignment": 'CENTER', "verticalAlignment": 'MIDDLE'}},
    {"userEnteredValue": {"stringValue": ""}},
    {"userEnteredValue": {"stringValue": "Date"},
     "userEnteredFormat": {"horizontalAlignment": 'CENTER', "verticalAlignment": 'MIDDLE'}},
    {"userEnteredValue": {"stringValue": "Description"},
     "userEnteredFormat": {"horizontalAlignment": 'CENTER', "verticalAlignment": 'MIDDLE'}},
    {"userEnteredValue": {"stringValue": "Expenses"},
     "userEnteredFormat": {"horizontalAlignment": 'CENTER', "verticalAlignment": 'MIDDLE'}},
    {"userEnteredValue": {"stringValue": ""}},
    {"userEnteredValue": {"stringValue": "Surplus"},
     "userEnteredFormat": {"horizontalAlignment": 'CENTER', "verticalAlignment": 'MIDDLE'}},
    {"userEnteredValue": {"stringValue": "Tot earnings"},
     "userEnteredFormat": {"horizontalAlignment": 'CENTER', "verticalAlignment": 'MIDDLE'}},
    {"userEnteredValue": {"stringValue": "Tot Expenses"},
     "userEnteredFormat": {"horizontalAlignment": 'CENTER', "verticalAlignment": 'MIDDLE'}},
]
