import os
from rest_framework import serializers

# Allowed extensions for OCR (add more if needed)
VALID_EXTS = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp'}

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        # ---- size (max 15 MB) ----
        if value.size > 15 * 1024 * 1024:
            raise serializers.ValidationError("File too large – max 15 MB.")

        # ---- extension ----
        _, ext = os.path.splitext(value.name)
        ext = ext.lower()
        if ext not in VALID_EXTS:
            raise serializers.ValidationError(
                f"Unsupported file type. Allowed: {', '.join(sorted(VALID_EXTS))}"
            )
        return value