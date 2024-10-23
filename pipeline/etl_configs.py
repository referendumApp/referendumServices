etl_configs = [
    {
        "source": "ls_state",
        "destination": "states",
        "transformations": [
            {
                "function": "keep_columns",
                "parameters": {"columns": ["state_id", "state_name"]},
            },
            {
                "function": "rename",
                "parameters": {"columns": {"state_id": "id", "state_name": "name"}},
            },
        ],
        "dataframe": None,
    },
    {
        "source": "ls_role",
        "destination": "roles",
        "transformations": [
            {
                "function": "keep_columns",
                "parameters": {"columns": ["role_id", "role_name"]},
            },
            {
                "function": "rename",
                "parameters": {"columns": {"role_id": "id", "role_name": "name"}},
            },
        ],
        "dataframe": None,
    },
    {
        "source": "ls_body",
        "destination": "legislative_bodys",
        "transformations": [
            {
                "function": "keep_columns",
                "parameters": {"columns": ["body_id", "state_id", "role_id"]},
            },
            {
                "function": "rename",
                "parameters": {"columns": {"body_id": "id"}},
            },
        ],
        "dataframe": None,
    },
    {
        "source": "ls_party",
        "destination": "partys",
        "transformations": [
            {
                "function": "keep_columns",
                "parameters": {"columns": ["party_id", "party_name"]},
            },
            {
                "function": "rename",
                "parameters": {"columns": {"party_id": "id", "party_name": "name"}},
            },
        ],
        "dataframe": None,
    },
    {
        "source": "ls_bill",
        "destination": "bills",
        "transformations": [
            {
                "function": "keep_columns",
                "parameters": {
                    "columns": [
                        "bill_id",
                        "title",
                        "description",
                        "state_id",
                        "body_id",
                        "bill_number",
                        "session_id",
                        "status_id",
                        "status_date",
                    ]
                },
            },
            {
                "function": "rename",
                "parameters": {
                    "columns": {
                        "bill_id": "id",
                        "bill_number": "identifier",
                        "body_id": "legislative_body_id",
                    }
                },
            },
            {
                "function": "duplicate",
                "parameters": {
                    "source_name": "id",
                    "destination_name": "legiscan_id",
                },
            },
        ],
        "dataframe": None,
    },
    {
        "source": "ls_people",
        "destination": "legislators",
        "transformations": [
            {
                "function": "keep_columns",
                "parameters": {
                    "columns": [
                        "people_id",
                        "name",
                        "party_id",
                        "district",
                    ]
                },
            },
            {
                "function": "rename",
                "parameters": {"columns": {"people_id": "id"}},
            },
            {
                "function": "duplicate",
                "parameters": {
                    "source_name": "id",
                    "destination_name": "legiscan_id",
                },
            },
        ],
        "dataframe": None,
    },
    {
        "source": "ls_committee",
        "destination": "committees",
        "transformations": [
            {
                "function": "keep_columns",
                "parameters": {
                    "columns": [
                        "committee_id",
                        "committee_body_id",
                        "committee_name",
                    ]
                },
            },
            {
                "function": "rename",
                "parameters": {
                    "columns": {
                        "committee_id": "id",
                        "committee_body_id": "legislative_body_id",
                        "committee_name": "name",
                    }
                },
            },
        ],
        "dataframe": None,
    },
    # {
    #     "source": "ls_bill_vote",
    #     "destination": "bill_actions",
    #     "transformations": [
    #         {
    #             "function": "keep_columns",
    #             "parameters": {
    #                 "columns": [
    #                     "bill_id",
    #                     "created",
    #                     "passed",
    #                 ]
    #             },
    #         },
    #         {
    #             "function": "rename",
    #             "parameters": {
    #                 "columns": {
    #                     "created": "date",
    #                     "passed": "type",
    #                 }
    #             },
    #         },
    #     ],
    #     "dataframe": None,
    # },
    # {
    #     "source": "ls_bill_sponsor",
    #     "destination": "bill_sponsors",
    #     "transformations": [
    #         {
    #             "function": "keep_columns",
    #             "parameters": {
    #                 "columns": ["bill_id", "people_id", "sponsor_type_id"]
    #                 ### bill_id has relationship with bill.id, which we create ??? ###
    #             },
    #         },
    #         {
    #             "function": "rename",
    #             "parameters": {"columns": {"people_id": "legislator_id"}},
    #         },
    #         {
    #             "function": "set_primary_sponsor",
    #             "parameters": {
    #                 "sponsor_type_column": "sponsor_type_id",
    #                 "is_primary_column": "is_primary"
    #             }
    #         }
    #     ],
    #     "dataframe": None,
    # },
]
