
import os

content = """{% extends 'base_mobile.html' %}
{% load static %}

{% block content %}
<div class="container mobile-container mt-3 pb-5 mb-5">
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-3">
        <a href="{% url 'operacional:mobile_os_list' %}" class="btn btn-outline-secondary btn-sm">
            <i class="fas fa-arrow-left"></i> Voltar
        </a>
        <span class="badge {% if os.status == 'IN_PROGRESS' %}bg-primary{% else %}bg-secondary{% endif %} badge-lg">
            {{ os.get_status_display }}
        </span>
    </div>

    <!-- Client Info Card -->
    <div class="card shadow-sm mb-3">
        <div class="card-body">
            <h5 class="card-title">{{ os.client.fantasy_name|default:os.client.name }}</h5>
            <p class="mb-1"><i class="fas fa-map-marker-alt text-danger"></i> {{ os.client.address }}, {{ os.client.number }} - {{ os.client.neighborhood }}</p>
            <p class="mb-1"><i class="fas fa-city"></i> {{ os.client.city }} / {{ os.client.state }}</p>
            <a href="https://maps.google.com/?q={{os.client.address}} {{os.client.number}} {{os.client.city}}"
                target="_blank" class="btn btn-outline-primary btn-sm mt-2 w-100">
                <i class="fas fa-directions"></i> Abrir no Maps
            </a>
        </div>
    </div>

    <!-- Description -->
    <div class="card shadow-sm mb-3">
        <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">Descrição do Serviço</h6>
            <p class="card-text">{{ os.description|linebreaksbr }}</p>
        </div>
    </div>

    <!-- Actions Area -->
    <div id="actions-area" class="d-grid gap-3">
        
        <!-- Mock GPS for development (Show FIRST on localhost) -->
        <script>
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                document.write(`
                    <div class="alert alert-warning border shadow-sm p-3 mb-2 text-center">
                        <h6 class="mb-2"><i class="fas fa-flask"></i> FERRAMENTA DE TESTE (PC)</h6>
                        <p class="small mb-2">Use este botão para simular o GPS de Recife e avançar na OS.</p>
                        <button class="btn btn-warning w-100 shadow-sm fw-bold" onclick="mockCheckin()">
                            SIMULAR GPS E INICIAR
                        </button>
                    </div>
                `);
            }
        </script>

        <!-- Check-in Button -->
        {% if os.status == 'PENDING' %}
        <button id="btn-checkin" class="btn btn-success btn-lg shadow" onclick="performCheckin()">
            <i class="fas fa-map-marked-alt"></i> Iniciar Check-in (GPS Real)
        </button>
        {% elif os.status == 'IN_PROGRESS' %}
        <div class="alert alert-success py-2 text-center">
            <i class="fas fa-check-circle"></i> Check-in realizado às {{ os.checkin_time|date:"H:i" }}
        </div>
        {% endif %}

        <!-- Photo Upload -->
        {% if os.status == 'IN_PROGRESS' %}
        <div class="card bg-light border-0">
            <div class="card-body text-center">
                <h6 class="mb-3">Registrar Fotos</h6>
                <div class="row g-2">
                    <div class="col-6">
                        <label class="btn btn-outline-primary w-100 py-3">
                            <i class="fas fa-camera fa-2x mb-2 d-block"></i>
                            Antes
                            <input type="file" hidden accept="image/*" capture="environment"
                                onchange="uploadPhoto(this, 'Antes')">
                        </label>
                    </div>
                    <div class="col-6">
                        <label class="btn btn-outline-success w-100 py-3">
                            <i class="fas fa-camera fa-2x mb-2 d-block"></i>
                            Depois
                            <input type="file" hidden accept="image/*" capture="environment"
                                onchange="uploadPhoto(this, 'Depois')">
                        </label>
                    </div>
                </div>
            </div>
        </div>

        <!-- Finish Button -->
        <a href="{% url 'operacional:service_order_finish_mobile' os.id %}" class="btn btn-dark btn-lg shadow mt-2">
            <i class="fas fa-signature"></i> Finalizar & Assinar
        </a>
        {% endif %}
    </div>

    <!-- Gallery Preview -->
    <div id="gallery-area" class="row mt-3 g-2">
        {% for anexo in os.anexos.all %}
        <div class="col-4">
            <img src="{{ anexo.file.url }}" class="img-fluid rounded shadow-sm border" alt="{{ anexo.type }}">
            <small class="d-block text-center text-muted" style="font-size: 10px;">{{ anexo.type }}</small>
        </div>
        {% endfor %}
    </div>

</div>

<!-- Loading Overlay -->
<div id="loading"
    style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999;"
    class="d-flex justify-content-center align-items-center">
    <div class="spinner-border text-light" role="status"></div>
</div>

<script>
    function showLoading() { document.getElementById('loading').style.display = 'flex'; }
    function hideLoading() { document.getElementById('loading').style.display = 'none'; }

    function mockCheckin() {
        console.log("Executando mockCheckin (Simulação)...");
        showLoading();
        const data = { lat: -8.0476, long: -34.8770 }; 
        
        fetch("{% url 'operacional:api_checkin' os.id %}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            console.log("Resposta do servidor recebida:", response.status);
            return response.json();
        })
        .then(data => {
            hideLoading();
            if (data.success) {
                console.log("Simulação de check-in realizada com sucesso!");
                location.reload(); 
            } else {
                console.error("Erro no servidor:", data.error);
                alert("Erro: " + data.error);
            }
        })
        .catch(err => {
            console.error("Erro de conexão:", err);
            hideLoading();
            alert("Erro de conexão com o servidor. Verifique o terminal do Django.");
        });
    }

    function performCheckin() {
        console.log("Iniciando performCheckin (GPS Real)...");
        if (!navigator.geolocation) {
            alert("Geolocalização não suportada.");
            return;
        }

        showLoading();
        navigator.geolocation.getCurrentPosition(
            (position) => {
                console.log("GPS Real obtido:", position.coords.latitude, position.coords.longitude);
                const data = {
                    lat: position.coords.latitude,
                    long: position.coords.longitude
                };

                fetch("{% url 'operacional:api_checkin' os.id %}", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': '{{ csrf_token }}'
                    },
                    body: JSON.stringify(data)
                })
                    .then(response => response.json())
                    .then(data => {
                        hideLoading();
                        if (data.success) {
                            location.reload(); 
                        } else {
                            alert("Erro no Check-in: " + data.error);
                        }
                    })
                    .catch(err => {
                        hideLoading();
                        alert("Erro de conexão com o servidor.");
                    });
            },
            (error) => {
                console.error("Erro GPS Real:", error);
                hideLoading();
                let msg = "Erro ao obter localização.";
                if (error.code === 1) msg = "Acesso ao GPS negado pelo usuário.";
                else if (error.code === 2) msg = "Posição GPS não disponível.";
                else if (error.code === 3) msg = "Tempo esgotado (Timeout) ao buscar GPS.";
                alert(msg + " Verifique se o GPS está ligado.");
            },
            {
                enableHighAccuracy: true,
                timeout: 30000, 
                maximumAge: 0
            }
        );
    }

    function uploadPhoto(input, type) {
        if (input.files && input.files[0]) {
            showLoading();
            const formData = new FormData();
            formData.append('photo', input.files[0]);
            formData.append('type', type);

            fetch("{% url 'operacional:api_upload_photo' os.id %}", {
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}'
                },
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (data.success) {
                        const gallery = document.getElementById('gallery-area');
                        const div = document.createElement('div');
                        div.className = 'col-4';
                        div.innerHTML = `
                        <img src="${data.url}" class="img-fluid rounded shadow-sm border">
                        <small class="d-block text-center text-muted" style="font-size: 10px;">${data.type}</small>
                    `;
                        gallery.prepend(div);
                    } else {
                        alert("Erro ao enviar foto: " + data.error);
                    }
                })
                .catch(err => {
                    hideLoading();
                    alert("Erro de conexão.");
                });
        }
    }
</script>

<style>
    .mobile-container {
        max-width: 600px;
    }
</style>
{% endblock %}
"""

path = r"g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\operacional\templates\operacional\mobile_os_detail.html"
with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"File updated and sanitized: {path}")
