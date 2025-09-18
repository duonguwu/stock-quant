        // Create chart for specific ticker and confidence level
        function createTickerChart(ticker, level, color) {
            const ctx = document.getElementById(`chart-${ticker}-${level}`).getContext('2d');
            const data = dashboardData[ticker];
            
            if (!data) return;
            
            const datasets = [];
            
            // Price line for this ticker only
            datasets.push({
                label: `${ticker} Price`,
                data: data.price_data.map(item => ({
                    x: new Date(item.timestamp.replace(' ', 'T') + ':00'), // Fix timestamp parsing
                    y: item.close
                })),
                borderColor: color,
                backgroundColor: 'transparent',
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 5,
                yAxisID: 'price',
                borderWidth: 3
            });
            
            // Add signals for this confidence level
            if (data.signals && data.signals[level]) {
                const signals = data.signals[level].signals;
                
                // BUY signals
                const buySignals = signals.filter(s => s.action === 'BUY');
                if (buySignals.length > 0) {
                    datasets.push({
                        label: `${ticker} BUY`,
                        data: buySignals.map(s => ({
                            x: new Date(s.timestamp.replace(' ', 'T') + ':00'), // Fix timestamp parsing
                            y: s.price
                        })),
                        backgroundColor: '#27ae60',
                        borderColor: '#27ae60',
                        pointStyle: 'triangle',
                        pointRadius: 12,
                        pointHoverRadius: 15,
                        showLine: false,
                        yAxisID: 'price'
                    });
                }
                
                // SELL signals  
                const sellSignals = signals.filter(s => s.action === 'SELL');
                if (sellSignals.length > 0) {
                    datasets.push({
                        label: `${ticker} SELL`,
                        data: sellSignals.map(s => ({
                            x: new Date(s.timestamp.replace(' ', 'T') + ':00'), // Fix timestamp parsing
                            y: s.price
                        })),
                        backgroundColor: '#e74c3c',
                        borderColor: '#e74c3c',
                        pointStyle: 'triangle',
                        pointRadius: 12,
                        pointHoverRadius: 15,
                        showLine: false,
                        yAxisID: 'price',
                        rotation: 180  // Tam giác ngược
                    });
                }
                
                // HOLD signals
                const holdSignals = signals.filter(s => s.action === 'HOLD');
                if (holdSignals.length > 0) {
                    datasets.push({
                        label: `${ticker} HOLD`,
                        data: holdSignals.map(s => ({
                            x: new Date(s.timestamp.replace(' ', 'T') + ':00'), // Fix timestamp parsing
                            y: s.price
                        })),
                        backgroundColor: '#95a5a6',
                        borderColor: '#95a5a6',
                        pointStyle: 'rect',
                        pointRadius: 8,
                        pointHoverRadius: 12,
                        showLine: false,
                        yAxisID: 'price'
                    });
                }
            }
            
            // Destroy existing chart if it exists
            const chartKey = `${ticker}-${level}`;
            if (charts[chartKey]) {
                charts[chartKey].destroy();
            }
            
            charts[chartKey] = new Chart(ctx, {
                type: 'line',
                data: { datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            enabled: true,
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'rgba(0, 0, 0, 0.9)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#3498db',
                            borderWidth: 2,
                            cornerRadius: 10,
                            padding: 15,
                            titleFont: {
                                size: 14,
                                weight: 'bold'
                            },
                            bodyFont: {
                                size: 12
                            },
                            callbacks: {
                                title: function(context) {
                                    const date = new Date(context[0].parsed.x);
                                    return `📅 ${date.toLocaleString('vi-VN', {
                                        year: 'numeric',
                                        month: '2-digit',
                                        day: '2-digit',
                                        hour: '2-digit',
                                        minute: '2-digit',
                                        second: '2-digit'
                                    })}`;
                                },
                                label: function(context) {
                                    const dataset = context.dataset;
                                    const value = context.parsed.y;
                                    const index = context.dataIndex;
                                    
                                    // Lấy thông tin chi tiết từ data gốc
                                    let tooltipText = `${dataset.label}: ${value.toFixed(0)} VND`;
                                    
                                    // Nếu là price line, hiển thị thêm thông tin OHLCV
                                    if (dataset.label.includes('Price')) {
                                        const priceData = data.price_data[index];
                                        if (priceData) {
                                            tooltipText = [
                                                `📊 ${ticker} - Giá đóng cửa`,
                                                `💰 Giá: ${value.toFixed(0)} VND`,
                                                `📈 Mở: ${priceData.open.toFixed(0)} VND`,
                                                `📉 Cao: ${priceData.high.toFixed(0)} VND`,
                                                `📉 Thấp: ${priceData.low.toFixed(0)} VND`,
                                                `📊 Khối lượng: ${priceData.volume.toLocaleString()} CP`
                                            ];
                                        }
                                    }
                                    
                                    // Nếu là signal, hiển thị thông tin signal
                                    if (dataset.label.includes('BUY') || dataset.label.includes('SELL') || dataset.label.includes('HOLD')) {
                                        const signals = data.signals[level].signals;
                                        const signalData = signals.find(s => 
                                            new Date(s.timestamp.replace(' ', 'T') + ':00').getTime() === context.parsed.x
                                        );
                                        
                                        if (signalData) {
                                            const signalType = signalData.action;
                                            const confidence = signalData.confidence || 'N/A';
                                            const volume = signalData.volume || 0;
                                            const changePct = signalData.change_pct || 0;
                                            
                                            tooltipText = [
                                                `🎯 ${signalType} Signal (${level.replace('conf_', '')}% Confidence)`,
                                                `💰 Giá: ${value.toFixed(0)} VND`,
                                                `📊 Confidence: ${(confidence * 100).toFixed(1)}%`,
                                                `📈 Volume: ${volume.toLocaleString()} CP`,
                                                `📊 Thay đổi: ${changePct.toFixed(2)}%`,
                                                `⏰ Thời gian: ${new Date(signalData.timestamp).toLocaleString('vi-VN')}`
                                            ];
                                        }
                                    }
                                    
                                    return tooltipText;
                                },
                                afterBody: function(context) {
                                    // Hiển thị thông tin bổ sung ở cuối tooltip
                                    const date = new Date(context[0].parsed.x);
                                    const timeInfo = date.toLocaleString('vi-VN', {
                                        weekday: 'long',
                                        year: 'numeric',
                                        month: 'long',
                                        day: 'numeric'
                                    });
                                    
                                    return [
                                        '',
                                        `📅 ${timeInfo}`,
                                        `⏰ Khung thời gian: 15 phút`,
                                        `📊 Nguồn: ${level.replace('conf_', '')}% Confidence Level`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                displayFormats: {
                                    hour: 'HH:mm',
                                    day: 'MM/dd'
                                }
                            },
                            title: {
                                display: true,
                                text: 'Time (15m intervals)'
                            }
                        },
                        price: {
                            type: 'linear',
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Price (VND)'
                            }
                        }
                    }
                }
            });
        }
