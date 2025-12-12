import pytest

def test_api_schema_discovery(client, auth_headers):
    """Discover what schema the API expects"""
    
    test_cases = [
        {
            "name": "Nested with camelCase",
            "data": {
                "nama": "Test",
                "durasi": {
                    "tanggalMulai": "2024-12-01",
                    "tanggalSelesai": "2024-12-07"
                },
                "anggaran": {
                    "jumlah": 5000000.0,
                    "mata_uang": "IDR"
                }
            }
        },
        {
            "name": "Nested with snake_case inside",
            "data": {
                "nama": "Test",
                "durasi": {
                    "tanggal_mulai": "2024-12-01",
                    "tanggal_selesai": "2024-12-07"
                },
                "anggaran": {
                    "jumlah": 5000000.0,
                    "mata_uang": "IDR"
                }
            }
        }
    ]
    
    for test in test_cases:
        response = client.post(
            "/api/perencanaan/",
            json=test["data"],
            headers=auth_headers
        )
        print(f"\n{test['name']}")
        print(f"Status: {response.status_code}")
        if response.status_code != 201:
            print(f"Error: {response.json()}")
        else:
            print("SUCCESS!")
            print(f"Response: {response.json()}")
            return  # Stop on first success
    
    pytest.fail("None of the formats worked!")