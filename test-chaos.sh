#!/bin/bash

# Payment System - Kaos Test Script
# Kullanım: ./test-chaos.sh [senaryo]

set -e

NAMESPACE="payment-chaos"
PAYMENT_URL="${PAYMENT_URL:-http://localhost:5002}"
INVENTORY_URL="${INVENTORY_URL:-http://localhost:5003}"
NOTIFICATION_URL="${NOTIFICATION_URL:-http://localhost:5004}"

# Renkli çıktı
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    printf "\n${BLUE}========================================${NC}\n"
    printf "${BLUE}%s${NC}\n" "$1"
    printf "${BLUE}========================================${NC}\n\n"
}

print_success() {
    printf "${GREEN}✓ %s${NC}\n" "$1"
}

print_warning() {
    printf "${YELLOW}⚠ %s${NC}\n" "$1"
}

print_error() {
    printf "${RED}✗ %s${NC}\n" "$1"
}

# Sağlık kontrolü
health_check() {
    print_header "Servis Sağlık Kontrolü"
    
    for service in "payment:$PAYMENT_URL" "inventory:$INVENTORY_URL" "notification:$NOTIFICATION_URL"; do
        name=$(echo $service | cut -d: -f1)
        url=$(echo $service | cut -d: -f2-3)
        
        if curl -s "$url/health" | grep -q "healthy"; then
            print_success "$name servisi sağlıklı"
        else
            print_error "$name servisine ulaşılamıyor"
        fi
    done
}

# Temel işlevsellik testi
basic_test() {
    print_header "Temel İşlevsellik Testi"
    
    echo "1. Ödeme işlemi test ediliyor..."
    start_time=$(date +%s%N)
    result=$(curl -s -X POST "$PAYMENT_URL/payment/process" \
        -H "Content-Type: application/json" \
        -d '{"amount": 100, "currency": "TRY", "product_id": "1"}')
    end_time=$(date +%s%N)
    latency=$(( (end_time - start_time) / 1000000 ))
    
    if echo "$result" | grep -q "payment_id"; then
        print_success "Ödeme işlemi başarılı (${latency}ms)"
    else
        print_error "Ödeme işlemi başarısız"
    fi
    
    echo "2. Stok kontrolü test ediliyor..."
    start_time=$(date +%s%N)
    result=$(curl -s "$INVENTORY_URL/check/1")
    end_time=$(date +%s%N)
    latency=$(( (end_time - start_time) / 1000000 ))
    
    if echo "$result" | grep -q "available"; then
        print_success "Stok kontrolü başarılı (${latency}ms)"
    else
        print_error "Stok kontrolü başarısız"
    fi
    
    echo "3. Zincirleme işlem test ediliyor..."
    start_time=$(date +%s%N)
    result=$(curl -s -X POST "$PAYMENT_URL/payment/chain" \
        -H "Content-Type: application/json" \
        -d '{"product_id": "1"}')
    end_time=$(date +%s%N)
    latency=$(( (end_time - start_time) / 1000000 ))
    
    echo "Sonuç: $result"
    print_success "Zincirleme işlem tamamlandı (${latency}ms)"
}

# Gecikme testi
delay_test() {
    print_header "Gecikme Testi (Kaos Aktifken)"
    
    echo "5 ardışık istek gönderiliyor..."
    total_latency=0
    
    for i in {1..5}; do
        start_time=$(date +%s%N)
        curl -s -X POST "$PAYMENT_URL/payment/chain" \
            -H "Content-Type: application/json" \
            -d '{"product_id": "1"}' > /dev/null
        end_time=$(date +%s%N)
        latency=$(( (end_time - start_time) / 1000000 ))
        total_latency=$((total_latency + latency))
        
        if [ $latency -gt 5000 ]; then
            print_warning "İstek $i: ${latency}ms (GECİKME TESPİT EDİLDİ)"
        else
            print_success "İstek $i: ${latency}ms"
        fi
    done
    
    avg_latency=$((total_latency / 5))
    printf "\n${YELLOW}Ortalama gecikme: ${avg_latency}ms${NC}\n"
}

# Paket kaybı testi
packet_loss_test() {
    print_header "Paket Kaybı Testi"
    
    echo "20 istek gönderiliyor..."
    success=0
    failed=0
    
    for i in {1..20}; do
        if curl -s --max-time 5 "$PAYMENT_URL/health" | grep -q "healthy"; then
            ((success++))
        else
            ((failed++))
        fi
    done
    
    printf "\n${GREEN}Başarılı: $success${NC} | ${RED}Başarısız: $failed${NC}\n"
    loss_rate=$((failed * 100 / 20))
    printf "${YELLOW}Paket kaybı oranı: %%${loss_rate}${NC}\n"
}

# Stres testi
stress_test() {
    print_header "Stres Testi (50 paralel istek)"
    
    start_time=$(date +%s)
    
    for i in {1..50}; do
        curl -s -X POST "$PAYMENT_URL/payment/process" \
            -H "Content-Type: application/json" \
            -d "{\"amount\": $i, \"product_id\": \"1\"}" > /dev/null &
    done
    wait
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    print_success "50 istek ${duration} saniyede tamamlandı"
    print_success "Saniyede ortalama: $((50 / (duration + 1))) istek"
}

# Kaos uygula
apply_chaos() {
    local scenario=$1
    print_header "Kaos Senaryosu Uygulanıyor: $scenario"
    
    case $scenario in
        "loss")
            kubectl apply -f chaos-experiments/02-packet-loss-80-percent.yaml
            print_success "%80 paket kaybı senaryosu uygulandı"
            ;;
        "stress")
            kubectl apply -f chaos-experiments/05-stress-chaos.yaml
            print_success "Stres senaryosu uygulandı"
            ;;
        *)
            print_error "Bilinmeyen senaryo: $scenario"
            echo "Kullanılabilir senaryolar: loss, stress"
            exit 1
            ;;
    esac
}

# Kaos temizle
cleanup_chaos() {
    print_header "Kaos Deneyleri Temizleniyor"
    
    kubectl delete networkchaos --all -n $NAMESPACE 2>/dev/null || true
    kubectl delete podchaos --all -n $NAMESPACE 2>/dev/null || true
    kubectl delete stresschaos --all -n $NAMESPACE 2>/dev/null || true
    kubectl delete workflow --all -n $NAMESPACE 2>/dev/null || true
    kubectl delete schedule --all -n $NAMESPACE 2>/dev/null || true
    
    print_success "Tüm kaos deneyleri temizlendi"
}

# Ana menü
show_menu() {
    echo ""
    echo "Payment System Kaos Test Aracı"
    echo "=============================="
    echo "1. Sağlık kontrolü"
    echo "2. Temel işlevsellik testi"
    echo "3. Paket kaybı testi"
    echo "4. Stres testi"
    echo "5. Kaos uygula (loss|stress)"
    echo "6. Kaos temizle"
    echo "7. Çıkış"
    echo ""
}

# Ana akış
case "${1:-menu}" in
    "health")
        health_check
        ;;
    "basic")
        basic_test
        ;;
    "loss")
        packet_loss_test
        ;;
    "stress")
        stress_test
        ;;
    "apply")
        apply_chaos "${2:-loss}"
        ;;
    "cleanup")
        cleanup_chaos
        ;;
    "menu")
        while true; do
            show_menu
            read -p "Seçiminiz: " choice
            case $choice in
                1) health_check ;;
                2) basic_test ;;
                3) packet_loss_test ;;
                4) stress_test ;;
                5) 
                    read -p "Senaryo (loss|stress): " scenario
                    apply_chaos "$scenario"
                    ;;
                6) cleanup_chaos ;;
                7) exit 0 ;;
                *) print_error "Geçersiz seçim" ;;
            esac
        done
        ;;
    *)
        echo "Kullanım: $0 [health|basic|loss|stress|apply <senaryo>|cleanup|menu]"
        exit 1
        ;;
esac
