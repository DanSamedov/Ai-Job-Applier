import sqlalchemy as sa


def StringEnum(enum_class, **kwargs):
    return sa.Enum(
        enum_class,
        native_enum=False,
        values_callable=lambda obj: [item.value for item in obj],
        **kwargs
    )