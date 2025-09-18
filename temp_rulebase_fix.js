                                    // Nếu là signal, hiển thị thông tin signal
                                    if (dataset.label.includes("BUY") || dataset.label.includes("SELL") || dataset.label.includes("HOLD")) {
                                        const signals = data.rulebase_signals;
                                        
                                        // Tìm signal gần nhất với thời điểm hover (trong vòng 15 phút)
                                        const hoverTime = context.parsed.x;
                                        const fifteenMinutes = 15 * 60 * 1000; // 15 phút tính bằng ms
                                        
                                        const signalData = signals.find(s => {
                                            const signalTime = new Date(s.timestamp.replace(" ", "T") + ":00").getTime();
                                            const timeDiff = Math.abs(signalTime - hoverTime);
                                            return timeDiff <= fifteenMinutes;
                                        });
                                        
                                        if (signalData) {
                                            const signalType = signalData.action;
                                            const volume = signalData.volume || 0;
                                            const createdAt = signalData.created_at || signalData.timestamp;
                                            
                                            tooltipText = [
                                                `🎯 ${signalType} Signal (Rule-Based)`,
                                                `💰 Giá: ${value.toFixed(0)} VND`,
                                                `📈 Volume: ${volume.toLocaleString()} CP`,
                                                `⏰ Thời gian: ${new Date(signalData.timestamp).toLocaleString("vi-VN")}`,
                                                `📅 Tạo lúc: ${new Date(createdAt).toLocaleString("vi-VN")}`
                                            ];
                                        } else {
                                            // Nếu không tìm thấy signal gần, hiển thị thông tin điểm chart
                                            tooltipText = [
                                                `📊 ${ticker} - Giá đóng cửa`,
                                                `💰 Giá: ${value.toFixed(0)} VND`,
                                                `⏰ Thời gian: ${new Date(hoverTime).toLocaleString("vi-VN")}`,
                                                `ℹ️ Không có signal trong vòng 15 phút`
                                            ];
                                        }
                                    }
