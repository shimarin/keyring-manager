PREFIX = $(HOME)/.local
INSTALL_BIN_DIR = $(PREFIX)/bin
INSTALL_ICONS_DIR = $(PREFIX)/share/icons/hicolor/1024x1024/apps
INSTALL_DESKTOP_DIR = $(PREFIX)/share/applications

APP_ID = dev.gemini.keyring-manager
APP_NAME = keyring-manager
ICON_NAME = $(APP_ID)
DESKTOP_FILE_NAME = $(APP_ID).desktop

.PHONY: all
all:
	@echo "Usage: make install"

.PHONY: install
install:
	@echo "Installing application to $(PREFIX)..."
	@echo
	@echo "==> Installing executable..."
	@mkdir -p $(INSTALL_BIN_DIR)
	@install -m 755 main.py $(INSTALL_BIN_DIR)/$(APP_NAME)
	@echo "  -> $(INSTALL_BIN_DIR)/$(APP_NAME)"

	@echo "==> Installing icon..."
	@mkdir -p $(INSTALL_ICONS_DIR)
	@install -m 644 $(ICON_NAME).png $(INSTALL_ICONS_DIR)/$(ICON_NAME).png
	@echo "  -> $(INSTALL_ICONS_DIR)/$(ICON_NAME).png"

	@echo "==> Installing desktop entry..."
	@mkdir -p $(INSTALL_DESKTOP_DIR)
	@echo "[Desktop Entry]" > $(INSTALL_DESKTOP_DIR)/$(DESKTOP_FILE_NAME)
	@echo "Version=1.0" >> $(INSTALL_DESKTOP_DIR)/$(DESKTOP_FILE_NAME)
	@echo "Type=Application" >> $(INSTALL_DESKTOP_DIR)/$(DESKTOP_FILE_NAME)
	@echo "Name=カーネルキーリング・マネージャー" >> $(INSTALL_DESKTOP_DIR)/$(DESKTOP_FILE_NAME)
	@echo "Comment=カーネルキーリングのエントリを管理するGTK4アプリケーション" >> $(INSTALL_DESKTOP_DIR)/$(DESKTOP_FILE_NAME)
	@echo "Exec=$(INSTALL_BIN_DIR)/$(APP_NAME)" >> $(INSTALL_DESKTOP_DIR)/$(DESKTOP_FILE_NAME)
	@echo "Icon=$(ICON_NAME)" >> $(INSTALL_DESKTOP_DIR)/$(DESKTOP_FILE_NAME)
	@echo "Categories=Utility;Security;" >> $(INSTALL_DESKTOP_DIR)/$(DESKTOP_FILE_NAME)
	@echo "Terminal=false" >> $(INSTALL_DESKTOP_DIR)/$(DESKTOP_FILE_NAME)
	@echo "  -> $(INSTALL_DESKTOP_DIR)/$(DESKTOP_FILE_NAME)"
	@echo
	@echo "Installation complete."
	@echo "Updating desktop database..."
	@update-desktop-database -q $(INSTALL_DESKTOP_DIR) || echo "Could not update desktop database. Please run it manually."


.PHONY: uninstall
uninstall:
	@echo "Uninstalling application from $(PREFIX)..."
	@echo
	@echo "==> Removing executable..."
	@rm -f $(INSTALL_BIN_DIR)/$(APP_NAME)
	@echo "  -> Removed $(INSTALL_BIN_DIR)/$(APP_NAME)"

	@echo "==> Removing icon..."
	@rm -f $(INSTALL_ICONS_DIR)/$(ICON_NAME).png
	@echo "  -> Removed $(INSTALL_ICONS_DIR)/$(ICON_NAME).png"

	@echo "==> Removing desktop entry..."
	@rm -f $(INSTALL_DESKTOP_DIR)/$(DESKTOP_FILE_NAME)
	@echo "  -> Removed $(INSTALL_DESKTOP_DIR)/$(DESKTOP_FILE_NAME)"
	@echo
	@echo "Uninstallation complete."
	@echo "Updating desktop database..."
	@update-desktop-database -q $(INSTALL_DESKTOP_DIR) || echo "Could not update desktop database. Please run it manually."
