class ZendeskOrganisation:
    "Represents an organisation in Zendesk"

    def __init__(self, parsed_dict: dict = None) -> None:
        if parsed_dict is not None:
            self.from_dict(parsed_dict)

        def from_dict(self, parsed_dict):
            "takes a dictionary and assigns the relevant parameters"
            print(parsed_dict)
            return
