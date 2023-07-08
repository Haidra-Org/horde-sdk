import json


def main():
    models_json = None
    with open("src/horde_sdk/models.json") as f:
        models = f.read()
        models_json = json.loads(models)

    # sort by value
    month_models_json = models_json["month"]
    month_models_json = dict(sorted(month_models_json.items(), key=lambda item: item[1], reverse=True))

    # print top 5 models
    for i, (model_name, model) in enumerate(month_models_json.items()):
        if i == 10:
            break
        print(f"{model_name}: {model}")


if __name__ == "__main__":
    main()
