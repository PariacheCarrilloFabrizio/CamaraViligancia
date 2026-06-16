from ultralytics import YOLO


def main() -> None:
    model = YOLO("models/fight/best.pt")

    print("Clases del modelo:")
    print(model.names)

    model.predict(
        source="videos/test_fight/pelea_01.mp4",
        conf=0.45,
        save=True,
        project="test_outputs",
        name="fight_prediction",
    )


if __name__ == "__main__":
    main()