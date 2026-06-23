# -----------------------------------------------------------------------------
# TAB 1: EXECUTIVE SUMMARY
# -----------------------------------------------------------------------------
with tab_summary:
    col_header, col_btn = st.columns([2, 1])
    with col_header:
        st.markdown("<h3 style='font-family:Playfair Display, serif; italic; margin: 0;'>Portfolio Vulnerability Indicators</h3>", unsafe_style_with_html=True)
    with col_btn:
        if not filtered_df.empty:
            # Dynamically converts the current filtered state of the dataset into CSV format
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Dataset (CSV)",
                data=csv_data,
                file_name=f"ecb_churn_filtered_{len(filtered_df)}_records.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.button("📥 Download Dataset (CSV)", disabled=True, use_container_width=True)
