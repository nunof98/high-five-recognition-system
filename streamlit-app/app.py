import html
import io

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from encrypted_csv_client import get_client
from pyvis.network import Network

# Admin password (change this or set in Streamlit secrets!)
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD")

# Page configuration
st.set_page_config(
    page_title="High Five Recognition",
    page_icon="✋",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        /* Push the header down to make room for brandline */
        header[data-testid="stHeader"] {
            top: 8px !important;
        }

        /* Inject brandline above the header */
        header[data-testid="stHeader"]::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 8px;
            z-index: 9999999;
            background-image: url('./app/static/brandline.png');
            background-size: cover;
            background-repeat: no-repeat;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Custom CSS for brand colors and styling
st.markdown(
    """
<style>
    .main {
        #background: linear-gradient(135deg, #FF9900 0%, #FFE79B 100%);
    }
    .stApp {
        #background: linear-gradient(135deg, #FF9900 0%, #FFE79B 100%);
    }
    div[data-testid="stForm"] {
        # background-color: white;
        background-color: var(--secondary-background-color);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    .success-card {
        # background-color: white;
        background-color: var(--secondary-background-color);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        margin: 1rem 0;
    }
    .color-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        text-transform: uppercase;
        border: 3px solid currentColor;
        margin: 1rem 0;
    }
    h1 {
        color: white;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .stTextArea textarea, .stTextInput input {
        # border: 2px solid;
        border-radius: 8px;
    }
    /* Streamlit wraps components.v1.html in a bordered/backgrounded iframe container; strip both so the mind map blends in */
    div[data-testid="stIFrame"], iframe {
        border: none !important;
        background: transparent !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Color mapping
CATEGORY_COLORS = {
    "collaboration_excellence": "#9E2896",
    "knowledge_growth": "#007BC0",
    "supplier_management": "#18837E",
    "performance_delivery": "#00884A",
}

# Left-to-right color stops sampled from static/brandline.png, used for the person-node ring in the mind map
BRANDLINE_GRADIENT_STOPS = [
    "#7A1F3D",
    "#D31F3C",
    "#5B2A8C",
    "#2E4A9E",
    "#3F97C9",
    "#2FAE6A",
    "#8DC63F",
]

# Fixed radius (px) of person nodes, matching their widthConstraint/heightConstraint (60) in build_relationship_network
PERSON_NODE_RADIUS = 30


def get_query_params():
    """Get parameters from URL query parameters"""
    try:
        query_params = st.query_params

        # Check for admin mode first
        if query_params.get("admin", None) is not None:
            return "admin", None

        # Otherwise get token and category
        token = query_params.get("token", None)
        category = query_params.get("category", None)
        return token, category
    except Exception:
        return None, None


def format_category(category: str) -> str:
    """Format snake_case category to display name"""
    return category.replace("_", " ").title()


def display_existing_message(data):
    """Display an existing High Five message"""
    st.markdown("# 🎉 High Five Already Given!")

    color_hex = CATEGORY_COLORS.get(data["Category"], "#333")

    st.markdown(
        f"""
    <div class="success-card">
        <div style="border-left: 4px solid {color_hex}; padding-left: 15px;">
            <div class="color-badge" style="color: {color_hex};">
                {format_category(data["Category"]).upper()} Token
            </div>
            <p style="font-size: 1.2em; margin: 15px 0; background-color: {color_hex}; color: white; border-radius: 8px; padding: 10px;">
                <strong>"{data["Message"]}"</strong>
            </p>
            <p style="color: #999; font-size: 0.8em; margin-top: 10px;">
                {data["Timestamp"]}
            </p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_new_token_form(token, category):
    """Display form for new High Five submission"""
    st.markdown("# ✋ Give Your High Five!")

    with st.form("highfive_form", clear_on_submit=True):
        # Display token category
        color_hex = CATEGORY_COLORS.get(category, "#333")

        # Inject dynamic CSS for input backgrounds matching category color
        st.markdown(
            f"""
            <style>
                .stTextArea textarea, .stTextInput input {{
                    border: 2px solid {color_hex} !important;
                }}
                .stTextArea textarea:focus, .stTextInput input:focus {{
                    background-color: {color_hex}20 !important;
                    border-color: {color_hex} !important;
                }}
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
        <div>
            <label style="font-weight: 600;">Token:</label>
            <div class="color-badge" style="color: {color_hex};">
                {format_category(category).upper()}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Message input
        message = st.text_area(
            "Your Recognition Message",
            placeholder="Write why this person deserves a High Five...",
            height=120,
            help="Share your appreciation and recognition",
        )

        # Name input
        submitted_by = st.text_input(
            "Your Name",
            placeholder="Enter your name",
            help="Who is giving this High Five?",
        )

        # Submit button
        submit_button = st.form_submit_button("Send High Five 🎉")

        if submit_button:
            if not message or not submitted_by:
                st.error("⚠️ Please fill in all fields")
                return False

            # Submit to CSV
            try:
                with st.spinner("Sending your High Five..."):
                    csv_client = get_client()
                    success = csv_client.add_token(
                        token=token,
                        category=category,
                        message=message,
                        submitted_by=submitted_by,
                    )

                if success:
                    st.session_state["submitted"] = True
                    st.rerun()
                else:
                    st.error("❌ This token has already been used!")
                    return False
            except Exception as e:
                st.error(f"❌ Error submitting: {str(e)}")
                return False

    return True


def show_success_message():
    """Display success message after submission"""
    st.markdown("# High Five Sent!")
    st.markdown(
        """
    <div class="success-card">
        <p style="text-align: center; font-size: 1.1em; color: #666;">
            Your recognition has been recorded. Thank you! 🎉
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_error_message(error_text):
    """Display error message"""
    st.markdown("# ❌ Oops!")
    st.markdown(
        f"""
    <div class="success-card">
        <p style="text-align: center; font-size: 1.1em; color: #666;">
            {error_text}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_card_carousel(df):
    """Display a continuously auto-scrolling ticker of submission cards (message + category color)"""
    if df.empty:
        st.info("No data yet!")
        return

    cards_html = "".join(
        f"""
        <div class="marquee-card" style="background-color: {CATEGORY_COLORS.get(row["Category"], "#333")}20; border-color: {CATEGORY_COLORS.get(row["Category"], "#333")};">
            <div class="marquee-category" style="color: {CATEGORY_COLORS.get(row["Category"], "#333")};">
                {format_category(row["Category"]).upper()}
            </div>
            <p>{html.escape(str(row["Message"]))}</p>
        </div>
        """
        for _, row in df.iterrows()
    )

    # Duplicate the track once so the -50% translateX loop point is seamless; speed scales with card count
    duration = max(20, len(df) * 5)
    st.markdown(
        f"""
        <style>
        .marquee-container {{
            overflow: hidden;
            width: 100%;
            mask-image: linear-gradient(90deg, transparent, black 5%, black 95%, transparent);
            -webkit-mask-image: linear-gradient(90deg, transparent, black 5%, black 95%, transparent);
        }}
        .marquee-track {{
            display: flex;
            width: max-content;
            animation: hf-marquee-scroll {duration}s linear infinite;
        }}
        .marquee-track:hover {{
            animation-play-state: paused;
        }}
        .marquee-card {{
            flex: 0 0 auto;
            width: 260px;
            margin: 0 0.75rem;
            padding: 1.5rem 1.25rem;
            border-radius: 15px;
            border: 2px solid;
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            text-align: center;
        }}
        .marquee-category {{
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.85em;
        }}
        .marquee-card p {{
            font-size: 1.05em;
            margin: 0.5rem 0 0;
        }}
        @keyframes hf-marquee-scroll {{
            from {{ transform: translateX(0); }}
            to {{ transform: translateX(-50%); }}
        }}
        </style>
        <div class="marquee-container">
            <div class="marquee-track">
                {cards_html}
                {cards_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_relationship_network(df) -> Network:
    """Build an interactive Category <-> Submission <-> Person (SubmittedBy) network"""
    # st.context.theme reflects the live client theme (incl. user overrides), unlike the static
    # st.get_option("theme.base") config default, matching how the card carousel reacts to theme
    try:
        is_dark = st.context.theme.type == "dark"
    except Exception:
        is_dark = st.get_option("theme.base") == "dark"
    label_color = "#FAFAFA" if is_dark else "#31333F"
    person_bg_color = "#000000" if is_dark else "#FFFFFF"

    net = Network(
        height="600px",
        width="100%",
        directed=True,
        bgcolor="rgba(0,0,0,0)",
        font_color=label_color,
        cdn_resources="in_line",
    )
    net.set_options(
        """
        {
          "physics": {
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
              "gravitationalConstant": -60,
              "centralGravity": 0.008,
              "springLength": 140,
              "springConstant": 0.05,
              "damping": 0.5
            },
            "minVelocity": 0.75
          },
          "nodes": {
            "shape": "dot",
            "borderWidth": 2
          },
          "edges": {
            "smooth": {"type": "continuous"},
            "color": {"opacity": 0.5},
            "width": 1
          },
          "interaction": {"hover": true}
        }
        """
    )

    seen_categories = set()
    seen_people = set()

    for idx, row in df.reset_index(drop=True).iterrows():
        category = row["Category"]
        person = str(row["SubmittedBy"]).strip()
        message = str(row["Message"])
        color_hex = CATEGORY_COLORS.get(category, "#333333")

        cat_id = f"cat::{category}"
        if category not in seen_categories:
            net.add_node(
                cat_id,
                label=format_category(category),
                shape="circle",
                color=color_hex,
                font={"color": "white", "size": 13, "bold": True},
                borderWidth=3,
                widthConstraint={"minimum": 100, "maximum": 100},
                heightConstraint={"minimum": 100, "maximum": 100},
            )
            seen_categories.add(category)

        person_id = f"person::{person}"
        if person not in seen_people:
            net.add_node(
                person_id,
                label=person,
                shape="circle",
                # solid theme-colored fill hides where edges terminate inside the node;
                # the gradient ring is painted on top via afterDrawing (see show_relationship_map)
                color={
                    "background": person_bg_color,
                    "border": person_bg_color,
                    "highlight": {
                        "background": person_bg_color,
                        "border": person_bg_color,
                    },
                    "hover": {"background": person_bg_color, "border": person_bg_color},
                },
                font={"color": label_color, "size": 11},
                # vis-network's circle shape clips edges using "size" (default 25), not widthConstraint,
                # so without this edges terminate inside our gradient ring instead of at its perimeter
                size=PERSON_NODE_RADIUS,
                widthConstraint={"minimum": 60, "maximum": 60},
                heightConstraint={"minimum": 60, "maximum": 60},
            )
            seen_people.add(person)

        # Submission node id falls back to row position since TokenID may repeat/be missing
        submission_id = f"sub::{row.get('TokenID') or idx}"
        net.add_node(
            submission_id,
            # pyvis falls back to the node id as the label when label is falsy, so use a blank space instead of ""
            label=" ",
            title=html.escape(message),  # tooltip is rendered as HTML by vis-network
            shape="dot",
            color=color_hex,
            size=8,
        )

        net.add_edge(person_id, submission_id, color=color_hex)
        net.add_edge(submission_id, cat_id, color=color_hex)

    return net


def show_relationship_map(df):
    """Display a mind map connecting each submission to its category and person"""
    if df.empty:
        st.info("No data yet!")
        return

    try:
        net = build_relationship_network(df)
        html_source = net.generate_html()
        # pyvis always loads Bootstrap from a CDN and wraps the network in a Bootstrap .card,
        # which has its own opaque white background/border independent of #mynetwork's own styling
        html_source = html_source.replace(
            "<head>",
            "<head><style>"
            "html, body { background-color: transparent !important; margin: 0; } "
            "#mynetwork, .card, .card-body { "
            "border: none !important; background-color: transparent !important; box-shadow: none !important; "
            "}"
            "</style>",
            1,
        )
        # Same best-effort theme guess as build_relationship_network, used only as a JS fallback
        # if reading the parent document's live CSS variables fails (see getLiveThemeColors below)
        try:
            is_dark = st.context.theme.type == "dark"
        except Exception:
            is_dark = st.get_option("theme.base") == "dark"
        fallback_text_color = "#FAFAFA" if is_dark else "#31333F"
        fallback_bg_color = "#000000" if is_dark else "#FFFFFF"

        # vis-network canvas doesn't support CSS gradients, so paint the brandline gradient ring
        # around each transparent person node manually after every network redraw
        gradient_stops_js = ", ".join(f'"{c}"' for c in BRANDLINE_GRADIENT_STOPS)
        ring_script = f"""
        <script type="text/javascript">
        (function() {{
            var GRADIENT_STOPS = [{gradient_stops_js}];
            var FALLBACK_RADIUS = {PERSON_NODE_RADIUS};
            var FALLBACK_TEXT_COLOR = "{fallback_text_color}";
            var FALLBACK_BG_COLOR = "{fallback_bg_color}";

            // Read the live theme colors straight from the parent app's CSS variables (same
            // source the card carousel relies on), since this iframe has no theme of its own
            // and Python-side theme detection can lag or be wrong right after a theme switch.
            function getLiveThemeColors() {{
                try {{
                    var parentStyle = window.parent.getComputedStyle(
                        window.parent.document.documentElement
                    );
                    var textColor = parentStyle.getPropertyValue("--text-color").trim();
                    var bgColor = parentStyle.getPropertyValue("--background-color").trim();
                    if (textColor && bgColor) {{
                        return {{ text: textColor, bg: bgColor }};
                    }}
                }} catch (e) {{
                    // cross-origin or unavailable; fall back to the server-rendered guess
                }}
                return {{ text: FALLBACK_TEXT_COLOR, bg: FALLBACK_BG_COLOR }};
            }}

            function attachPersonRingRenderer() {{
                if (typeof network === "undefined" || typeof nodes === "undefined") {{
                    setTimeout(attachPersonRingRenderer, 50);
                    return;
                }}
                var personIds = nodes.getIds().filter(function (id) {{
                    return String(id).indexOf("person::") === 0;
                }});
                if (personIds.length === 0) return;

                var colors = getLiveThemeColors();
                nodes.update(personIds.map(function (id) {{
                    return {{
                        id: id,
                        color: {{
                            background: colors.bg,
                            border: colors.bg,
                            highlight: {{ background: colors.bg, border: colors.bg }},
                            hover: {{ background: colors.bg, border: colors.bg }},
                        }},
                        font: {{ color: colors.text, size: 11 }},
                    }};
                }}));

                network.on("afterDrawing", function (ctx) {{
                    personIds.forEach(function (id) {{
                        var nodeObj = network.body.nodes[id];
                        if (!nodeObj) return;
                        // read the node's own post-layout box so the ring always matches the
                        // (invisible) circle vis-network actually clips edges against
                        var shape = nodeObj.shape;
                        var radius = (shape && shape.width)
                            ? Math.max(shape.width, shape.height) / 2
                            : FALLBACK_RADIUS;
                        var x = nodeObj.x;
                        var y = nodeObj.y;
                        var gradient = ctx.createLinearGradient(x - radius, y, x + radius, y);
                        GRADIENT_STOPS.forEach(function (color, i) {{
                            gradient.addColorStop(i / (GRADIENT_STOPS.length - 1), color);
                        }});
                        ctx.save();
                        ctx.beginPath();
                        ctx.arc(x, y, radius, 0, 2 * Math.PI);
                        ctx.lineWidth = 3;
                        ctx.strokeStyle = gradient;
                        ctx.stroke();
                        ctx.restore();
                    }});
                }});
                network.redraw();
            }}
            attachPersonRingRenderer();
        }})();
        </script>
        """
        html_source = html_source.replace("</body>", ring_script + "</body>", 1)
        components.html(html_source, height=650, scrolling=True)
    except Exception as e:
        st.error(f"Error rendering relationship map: {str(e)}")


def show_admin_page():
    """Display admin page for viewing and managing data"""
    st.markdown("# 🔐 Admin Dashboard")

    # Password protection
    password = st.text_input("Enter admin password:", type="password")
    if password != ADMIN_PASSWORD:
        if password:
            st.error("❌ Incorrect password")
        st.stop()

    if not st.session_state.get("access_granted_shown", False):
        st.session_state["access_granted_shown"] = True

    try:
        csv_client = get_client()
        df = csv_client.get_all_data()

        if df.empty:
            st.info("No data yet!")
        else:
            tab_overview, tab_table = st.tabs(["🃏 Cards & Mind Map", "📋 Table"])

            with tab_overview:
                show_card_carousel(df)
                st.markdown("---")
                st.markdown("### Relationship Map")
                show_relationship_map(df)

            with tab_table:
                st.markdown(f"### Total Submissions: {len(df)}")

                # Add a selection column for deletion
                df_display = df.copy()
                df_display.insert(0, "Select", False)

                # Display editable dataframe with checkboxes
                st.markdown("#### All Submissions")

                edited_df = st.data_editor(
                    df_display,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Select": st.column_config.CheckboxColumn(
                            "Select",
                            help="Select records to delete",
                            default=False,
                        )
                    },
                    disabled=[
                        "TokenID",
                        "Category",
                        "Message",
                        "SubmittedBy",
                        "Timestamp",
                    ],
                )

                # Delete selected records
                selected_rows = edited_df[edited_df["Select"]]

                if len(selected_rows) > 0:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button(
                            f"🗑️ Delete {len(selected_rows)} Record(s)",
                            width="stretch",
                        ):
                            # Get indices of selected rows
                            indices_to_delete = selected_rows.index.tolist()

                            csv_client.delete_rows(indices_to_delete)

                            st.success(
                                f"✅ Successfully deleted {len(selected_rows)} record(s)!"
                            )
                            st.rerun()

                # Delete all data button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button(
                        "🗑️ Delete ALL Data", type="secondary", width="stretch"
                    ):
                        if st.session_state.get("confirm_delete_all", False):
                            csv_client.delete_all()
                            st.session_state["confirm_delete_all"] = False
                            st.success("✅ All data deleted!")
                            st.rerun()
                        else:
                            st.session_state["confirm_delete_all"] = True
                            st.rerun()

                if st.session_state.get("confirm_delete_all", False):
                    st.warning(
                        "⚠️ Are you sure? Click **Delete ALL Data** again to confirm."
                    )

                st.markdown("---")

                # Centered download buttons
                st.markdown("#### Download Data")
                spacer1, col1, col2, spacer2 = st.columns([1, 2, 2, 1])
                with col1:
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name="highfive_data.csv",
                        mime="text/csv",
                        width="stretch",
                    )
                with col2:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df.to_excel(writer, index=False, sheet_name="HighFives")
                    st.download_button(
                        label="📥 Download Excel",
                        data=buffer.getvalue(),
                        file_name="highfive_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width="stretch",
                    )

                st.markdown("---")

                # Statistics
                st.markdown("### Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(
                        f"<div style='text-align:center;'><b>Total High Fives</b><br><span style='font-size:1.5em'>{len(df)}</span></div>",
                        unsafe_allow_html=True,
                    )
                with col2:
                    category_counts = df["Category"].value_counts()
                    most_popular_raw = (
                        category_counts.index[0] if not category_counts.empty else None
                    )
                    most_popular = (
                        format_category(most_popular_raw) if most_popular_raw else "N/A"
                    )
                    color_hex = CATEGORY_COLORS.get(most_popular_raw, "#333")
                    st.markdown(
                        f"<div style='text-align:center;'><b>Most Popular Category</b><br>"
                        f"<span style='font-size:1.5em; color:{color_hex}'>{most_popular}</span></div>",
                        unsafe_allow_html=True,
                    )
                with col3:
                    recent = (
                        str(df.tail(1)["Timestamp"].values[0])
                        if not df.empty
                        else "N/A"
                    )
                    st.markdown(
                        f"<div style='text-align:center;'><b>Most Recent</b><br><span style='font-size:1.1em'>{recent}</span></div>",
                        unsafe_allow_html=True,
                    )

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")


def show_admin_button():
    """Display admin button in sidebar"""
    with st.sidebar:
        if st.button("🔐 Admin", key="admin_access_btn"):
            st.session_state["show_admin"] = True
            st.rerun()


def main():
    """Main application logic"""

    # Check for admin mode via URL param or session state
    token, category = get_query_params()
    if token == "admin" or st.session_state.get("show_admin", False):
        show_admin_page()
        return

    # Show admin button on main pages
    show_admin_button()

    # Validate parameters
    if not token or not category:
        show_error_message("Invalid QR code. Missing token or category parameter.")
        st.stop()

    # Check if form was just submitted
    if st.session_state.get("submitted", False):
        show_success_message()
        st.stop()

    # Initialize CSV client and check token
    try:
        with st.spinner("Checking your High Five token..."):
            csv_client = get_client()
            existing_data = csv_client.check_token(token)

        if existing_data:
            # Token exists - display the message
            display_existing_message(existing_data)
        else:
            # New token - show form
            show_new_token_form(token, category)

    except Exception as e:
        show_error_message(
            f"Unable to connect to the server. Please try again later.<br><small>Error: {str(e)}</small>"
        )


if __name__ == "__main__":
    main()
