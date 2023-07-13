query_ebay_listing = """
{
    ebayListing {
    title,
    winningBid,
    predictedGenericId,
    databaseId
    }
}
"""

query_listing_feedback = """
{
    listingFeedback (userId: 10) {
    userId,
    userComment,
    dateCreated
    }
}
"""

query_listing_feedback_id = """
    {
        ebayListing (databaseId: 1) {
            title,
            winningBid,
            predictedGenericId,
            databaseId
        }
    }
"""

mutation_update_listing_feedback = """
    mutation {
        createUpdateListingFeedback(ebaylistingId:12, isCorrect:true, userComment:"General Kenobi wrote this comment")
            {
                ok
                debug
            }
        }
"""