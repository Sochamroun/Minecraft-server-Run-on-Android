#!/data/data/com.termux/files/usr/bin/bash

echo "================================"
echo "     Java Runtime Selector"
echo "================================"
echo "1) Java 21"
echo "2) Java 25"
echo "0) Exit"
echo "================================"
read -rp "Choose Java [0-2]: " choice

case "$choice" in
    1)
        JAVA_PATH="$PREFIX/lib/jvm/java-21-openjdk/bin/java"
        ;;
    2)
        JAVA_PATH="$PREFIX/lib/jvm/java-25-openjdk/bin/java"
        ;;
    0)
        exit 0
        ;;
    *)
        echo "Invalid choice!"
        exit 1
        ;;
esac

# Check Java executable
if [ ! -x "$JAVA_PATH" ]; then
    echo "Error: Java not found!"
    echo "$JAVA_PATH"
    exit 1
fi

# Switch Java version
update-alternatives --set java "$JAVA_PATH" || exit 1

echo
echo "Selected Java version:"
java -version
